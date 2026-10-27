from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from drf_spectacular.utils import extend_schema
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer
from .guest import create_guest_session, claim_guest_data_for_user, discard_guest_session, is_guest_user
from apps.audit.services import log_audit_event

class GuestSessionView(views.APIView):
    """
    Manages isolated guest sessions for visitors to explore resume analysis,
    skill matching, and career roadmaps without an upfront account.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # If user is already authenticated with a valid guest session, return it
        if request.user and request.user.is_authenticated:
            if is_guest_user(request.user):
                token, _ = Token.objects.get_or_create(user=request.user)
                return Response({
                    'token': token.key,
                    'user_id': str(request.user.id),
                    'is_guest': True,
                    'message': 'Active guest session reused.'
                }, status=status.HTTP_200_OK)
            else:
                # Registered user already logged in
                return Response({
                    'user_id': str(request.user.id),
                    'is_guest': False,
                    'message': 'User is already registered and authenticated.'
                }, status=status.HTTP_200_OK)

        # Generate a new isolated guest session
        guest_user, token = create_guest_session()
        log_audit_event(
            user=guest_user,
            event_type='GUEST_SESSION_CREATED',
            metadata={'guest_id': str(guest_user.id)}
        )
        return Response({
            'token': token.key,
            'user_id': str(guest_user.id),
            'is_guest': True,
            'message': 'New isolated guest session created.'
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        token_key = request.headers.get('X-Guest-Token') or request.auth.key if request.auth else None
        if not token_key and request.headers.get('Authorization'):
            auth_parts = request.headers.get('Authorization').split()
            if len(auth_parts) == 2 and auth_parts[0] in ('Token', 'Bearer'):
                token_key = auth_parts[1]

        if not token_key:
            return Response({'error': 'No guest token provided.'}, status=status.HTTP_400_BAD_REQUEST)

        discarded = discard_guest_session(token_key)
        return Response({
            'discarded': discarded,
            'message': 'Guest session data and physical files have been purged.' if discarded else 'No active guest session found to discard.'
        }, status=status.HTTP_200_OK)

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=UserRegistrationSerializer, responses={201: UserProfileSerializer})
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            log_audit_event(user=user, event_type='AUTH_REGISTER', metadata={'email': user.email})

            # Check if registering from a guest session; transfer work seamlessly
            guest_token = request.headers.get('X-Guest-Token') or request.data.get('guest_token')
            claimed_count = 0
            if guest_token:
                claimed_count = claim_guest_data_for_user(guest_token, user)

            return Response({
                'token': token.key,
                'user': UserProfileSerializer(user).data,
                'claimed_guest_items': claimed_count,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=UserLoginSerializer, responses={200: UserProfileSerializer})
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            log_audit_event(user=user, event_type='AUTH_LOGIN', metadata={'email': user.email})

            # Check if logging into an account from a guest session; claim any work created as a guest
            guest_token = request.headers.get('X-Guest-Token') or request.data.get('guest_token')
            claimed_count = 0
            if guest_token:
                claimed_count = claim_guest_data_for_user(guest_token, user)

            return Response({
                'token': token.key,
                'user': UserProfileSerializer(user).data,
                'claimed_guest_items': claimed_count,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        Token.objects.filter(user=user).delete()
        logout(request)
        log_audit_event(user=user, event_type='AUTH_LOGOUT', metadata={'email': user.email})
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

class UserProfileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: UserProfileSerializer})
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        data = serializer.data
        data['is_guest'] = is_guest_user(request.user)
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
