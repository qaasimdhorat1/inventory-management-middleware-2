"""
Serializers for user authentication and profile management.

Handles registration, login, profile viewing/editing,
and password change with full server-side validation.
"""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password confirmation.
    Enforces strong password validation and unique email requirement.
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'password', 'password2',
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value: str) -> str:
        """Ensure email is unique across all users."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        """Ensure both passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data: dict) -> User:
        """Create user with hashed password."""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing and updating user profile.
    Password and username are read-only for security.
    """

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'date_joined',
        )
        read_only_fields = ('id', 'username', 'date_joined')

    def validate_email(self, value: str) -> str:
        """Ensure updated email is unique (excluding current user)."""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change with old password verification.
    """

    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    new_password2 = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs: dict) -> dict:
        """Ensure new passwords match."""
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "New password fields didn't match."}
            )
        return attrs

class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset via username and email verification.
    Allows users who have forgotten their password to reset it
    by verifying their identity through username and email.
    """

    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    new_password2 = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs: dict) -> dict:
        """Ensure new passwords match and user exists with matching email."""
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "New password fields didn't match."}
            )
        if not User.objects.filter(
            username=attrs['username'],
            email=attrs['email'],
        ).exists():
            raise serializers.ValidationError(
                "No account found with this username and email combination."
            )
        return attrs