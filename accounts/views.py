"""
Views for user authentication and profile management.

Provides registration, profile retrieval/update, and password change
endpoints with appropriate permissions and error handling.
"""

from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ChangePasswordSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Public endpoint for user registration.
    Returns user data on successful registration.
    """

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/auth/profile/
    PUT/PATCH /api/auth/profile/
    Authenticated endpoint for viewing and updating user profile.
    """

    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self) -> User:
        """Return the currently authenticated user."""
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Authenticated endpoint for changing password.
    Requires old password verification.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"old_password": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(
            {"message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )