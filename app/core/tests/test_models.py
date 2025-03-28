"""Tests for models."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from ..models import Recipe, Tag, Ingredient


def create_user(email='user@example.com', password='testpassword'):
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """Test creating a user with en email is successful"""
        email = 'test@example.com'
        password = 'testpassword'

        user = create_user(email=email, password=password)

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
            user = create_user(
                email=email,
                password="testpassword"
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """ Test that creating a user without an email raises a ValueError"""

        with self.assertRaises(ValueError):
            create_user('', password='testpassword')

    def test_create_superuser(self):
        """Test creating a superuser"""

        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='testpassword'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_new_recipe(self):
        """Test creating a new recipe is successful"""

        user = create_user(
            email='user@example.com',
            password='testpassword'

        )

        recipe = Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal("5.50"),
            description='Sample recipe description'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test crating a tag is successful"""

        user = create_user()

        name = 'Vegan'

        tag = Tag.objects.create(user=user, name=name)

        self.assertEqual(tag.name, name)
        self.assertEqual(str(tag), name)

    def test_create_ingredient(self):
        """Test creating ingredient is successful"""

        user = create_user()

        ingredient = Ingredient.objects.create(user=user, name='Ingredient1')

        self.assertEqual(ingredient.name, str(ingredient))