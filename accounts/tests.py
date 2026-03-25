"""
Tests for user authentication and profile management.

Covers registration, login, profile operations, and password changes
with both valid and invalid inputs to ensure edge case handling.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class RegisterViewTests(TestCase):
    """Tests for user registration endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }

    def test_register_success(self) -> None:
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_register_password_mismatch(self) -> None:
        """Test registration fails when passwords don't match."""
        data = self.valid_data.copy()
        data['password2'] = 'DifferentPass123!'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_duplicate_email(self) -> None:
        """Test registration fails with duplicate email."""
        self.client.post(self.register_url, self.valid_data)
        data = self.valid_data.copy()
        data['username'] = 'testuser2'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self) -> None:
        """Test registration fails with duplicate username."""
        self.client.post(self.register_url, self.valid_data)
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self) -> None:
        """Test registration fails with weak password."""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['password2'] = '123'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self) -> None:
        """Test registration fails when required fields are missing."""
        response = self.client.post(self.register_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email(self) -> None:
        """Test registration fails with invalid email format."""
        data = self.valid_data.copy()
        data['email'] = 'not-an-email'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTests(TestCase):
    """Tests for JWT login endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.login_url = '/api/auth/login/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )

    def test_login_success(self) -> None:
        """Test successful login returns access and refresh tokens."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self) -> None:
        """Test login fails with incorrect password."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPass123!',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self) -> None:
        """Test login fails for non-existent user."""
        response = self.client.post(self.login_url, {
            'username': 'nouser',
            'password': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileViewTests(TestCase):
    """Tests for user profile endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.profile_url = '/api/auth/profile/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self) -> None:
        """Test retrieving authenticated user profile."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_update_profile(self) -> None:
        """Test updating user profile fields."""
        response = self.client.patch(self.profile_url, {
            'first_name': 'Updated',
            'last_name': 'Name',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')

    def test_profile_unauthenticated(self) -> None:
        """Test profile access denied without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_email_duplicate(self) -> None:
        """Test profile update fails with duplicate email."""
        User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!',
        )
        response = self.client.patch(self.profile_url, {
            'email': 'other@example.com',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordViewTests(TestCase):
    """Tests for password change endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.change_password_url = '/api/auth/change-password/'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self) -> None:
        """Test successful password change."""
        response = self.client.post(self.change_password_url, {
            'old_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!',
            'new_password2': 'NewSecurePass456!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass456!'))

    def test_change_password_wrong_old(self) -> None:
        """Test password change fails with wrong current password."""
        response = self.client.post(self.change_password_url, {
            'old_password': 'WrongPass123!',
            'new_password': 'NewSecurePass456!',
            'new_password2': 'NewSecurePass456!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self) -> None:
        """Test password change fails when new passwords don't match."""
        response = self.client.post(self.change_password_url, {
            'old_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!',
            'new_password2': 'DifferentPass789!',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated(self) -> None:
        """Test password change denied without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.change_password_url, {
            'old_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!',
            'new_password2': 'NewSecurePass456!',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)