from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from drf_spectacular.utils import extend_schema
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer
from apps.audit.services import log_audit_event

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=UserRegistrationSerializer, responses={201: UserProfileSerializer})
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            log_audit_event(user=user, event_type='AUTH_REGISTER', metadata={'email': user.email})
            return Response({
                'token': token.key,
                'user': UserProfileSerializer(user).data,
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
            return Response({
                'token': token.key,
                'user': UserProfileSerializer(user).data,
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
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
