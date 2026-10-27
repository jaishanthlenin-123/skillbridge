from django.core.management.base import BaseCommand
from apps.accounts.guest import cleanup_expired_guest_sessions

class Command(BaseCommand):
    help = 'Safely purges expired temporary guest accounts and their private storage files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Maximum age of guest sessions in hours before deletion (default: 24).'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        self.stdout.write(f"Scanning for guest sessions older than {hours} hours...")
        count = cleanup_expired_guest_sessions(max_age_hours=hours)
        self.stdout.write(self.style.SUCCESS(f"Successfully cleaned up {count} expired guest sessions."))
