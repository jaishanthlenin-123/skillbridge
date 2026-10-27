import secrets
import logging
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from apps.resumes.models import Resume
from apps.matches.models import MatchResult
from apps.roadmaps.models import Roadmap
from apps.resumes.storage import delete_private_file

logger = logging.getLogger(__name__)
User = get_user_model()

GUEST_EMAIL_DOMAIN = 'guest.skillbridge.local'
GUEST_MAX_RESUMES = 3
GUEST_SESSION_TTL_HOURS = 24

def is_guest_user(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return str(user.email).endswith(f'@{GUEST_EMAIL_DOMAIN}')

def create_guest_session() -> tuple[User, Token]:
    """
    Creates an isolated, unguessable temporary guest account and auth token.
    No permanent credentials or personal info are required.
    """
    random_id = secrets.token_hex(16)
    guest_email = f"guest_{random_id}@{GUEST_EMAIL_DOMAIN}"
    
    guest_user = User.objects.create_user(
        email=guest_email,
        password=None,
        first_name='Guest',
        last_name='Visitor'
    )
    token, _ = Token.objects.get_or_create(user=guest_user)
    logger.info(f"Generated new guest session for user ID {guest_user.id}")
    return guest_user, token

def claim_guest_data_for_user(guest_token_key: str, target_user: User) -> int:
    """
    Transfers all resumes, matches, and roadmaps from a guest session
    to a permanent registered user account upon login or registration.
    """
    if not guest_token_key or not target_user:
        return 0

    try:
        token_obj = Token.objects.select_related('user').get(key=guest_token_key)
        guest_user = token_obj.user
        if not is_guest_user(guest_user) or guest_user.id == target_user.id:
            return 0

        # Transfer resumes
        resumes_count = Resume.objects.filter(owner=guest_user).update(owner=target_user)
        # Transfer matches
        matches_count = MatchResult.objects.filter(owner=guest_user).update(owner=target_user)
        # Transfer roadmaps
        roadmaps_count = Roadmap.objects.filter(owner=guest_user).update(owner=target_user)

        total_transferred = resumes_count + matches_count + roadmaps_count
        logger.info(
            f"Successfully claimed {total_transferred} items from guest {guest_user.id} to user {target_user.email}"
        )

        # Remove temporary guest user and token
        token_obj.delete()
        guest_user.delete()
        return total_transferred
    except Token.DoesNotExist:
        return 0
    except Exception as exc:
        logger.warning(f"Error claiming guest session data: {exc}")
        return 0

def discard_guest_session(guest_token_key: str) -> bool:
    """
    Discards a guest session, purging all uploaded files and associated records.
    """
    if not guest_token_key:
        return False
    try:
        token_obj = Token.objects.select_related('user').get(key=guest_token_key)
        guest_user = token_obj.user
        if not is_guest_user(guest_user):
            return False

        # Purge physical resume files
        for resume in Resume.objects.filter(owner=guest_user):
            delete_private_file(resume.private_storage_key)

        token_obj.delete()
        guest_user.delete()
        logger.info(f"Purged guest session data for user {guest_user.id}")
        return True
    except Token.DoesNotExist:
        return False
    except Exception as exc:
        logger.warning(f"Failed to discard guest session: {exc}")
        return False

def cleanup_expired_guest_sessions(max_age_hours: int = GUEST_SESSION_TTL_HOURS) -> int:
    """
    Deletes all guest sessions older than max_age_hours, safely purging disk storage.
    Strictly ignores registered users (never touches non-guest accounts).
    """
    cutoff = timezone.now() - timedelta(hours=max_age_hours)
    expired_guests = User.objects.filter(
        email__endswith=f'@{GUEST_EMAIL_DOMAIN}',
        created_at__lt=cutoff
    )

    count = 0
    for guest in expired_guests:
        for resume in Resume.objects.filter(owner=guest):
            delete_private_file(resume.private_storage_key)
        guest.delete()
        count += 1

    if count > 0:
        logger.info(f"Cleaned up {count} expired guest sessions older than {max_age_hours} hours.")
    return count
