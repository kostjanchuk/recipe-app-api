"""Tests for models."""
from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """Test creating a user with en email is successful"""
        email = 'test@example.com'
        password = 'testpassword'

        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email normalized for new user"""

        email_lst = [
            ["test@EXAMPLE.com", "test@example.com"],
            ["Test2@EXAMPLE.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@ExamplE.com", "test4@example.com"],
        ]

        for email, expected in email_lst:
            user = get_user_model().objects.create_user(
                email=email,
                password="testpassword"
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """ Test that creating a user without an email raises a ValueError"""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', password='testpassword')

    def test_create_superuser(self):
        """Test creating a superuser"""

        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='testpassword'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)