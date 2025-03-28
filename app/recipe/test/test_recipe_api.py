"""
Tests for recipe APIs
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from ..serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample title',
        'description': 'Sample description',
        'time_minutes': 5,
        'price': Decimal('5.25'),
        'link': 'http://example.com/recipe.pdf'
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITest(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = create_user(email='user@example.com',
                                password='testpassword')

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user"""

        user = get_user_model().objects.create_user(
            email='user2@example.com',
            password='testpassword'
        )

        create_recipe(user=user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""

        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating recipe"""

        payload = {
            'title': 'Sample title',
            'description': 'Sample description',
            'time_minutes': 5,
            'price': Decimal('5.25'),
            'link': 'http://example.com/recipe.pdf'
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""

        original_link = 'http://example.com/recipe.pdf'
        recipe = create_recipe(self.user, link=original_link)

        payload = {
            'title': 'Sample title update',
            'description': 'Sample description update'
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.link, original_link)
        self.assertEqual(payload['title'], recipe.title)
        self.assertEqual(payload['description'], recipe.description)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of a recipe"""

        recipe = create_recipe(user=self.user)

        payload = {
            'title': 'Sample update title',
            'description': 'Sample update description',
            'time_minutes': 6,
            'price': Decimal('6.25'),
            'link': 'http://example.com/recipe.pdf'
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error"""

        recipe = create_recipe(user=self.user)

        new_user = create_user(
            email='otheruser@example.com',
            password='otherpassword'
        )

        url = detail_url(recipe.id)
        self.client.patch(url, {'user': new_user.id})
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Tests deleting a recipe successful"""

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another users recipe gives error"""

        another_user = create_user(email='other@xample.com',
                                   password='testpassword')

        recipe = create_recipe(user=another_user)

        url = detail_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_new_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title': 'Sample update title',
            'time_minutes': 6,
            'price': Decimal('6.25'),
            'tags': [{'name': 'Tag1'}, {'name': 'Tag2'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(
                name=tag['name'], user=self.user).exists())

    def test_create_recipe_with_existing_tag(self):
        """Test creating recipe with existing tag"""

        sample_tag = 'SampleTag'

        tag = Tag.objects.create(name=sample_tag, user=self.user)

        payload = {
            'title': 'Sample update title',
            'time_minutes': 6,
            'price': Decimal('6.25'),
            'tags': [{'name': 'SampleTag'}, {'name': 'Tag2'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())

        for tag in payload['tags']:
            self.assertTrue(recipe.tags.filter(name=tag['name']).exists())

    def test_create_tag_on_update(self):
        """Test creating tag when update recipe"""

        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Tag1'}]}

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user)

        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""

        tag1 = Tag.objects.create(user=self.user, name='Tag1')

        recipe = create_recipe(user=self.user)

        recipe.tags.add(tag1)

        tag2 = Tag.objects.create(user=self.user, name='Tag2')

        payload = {'tags': [{'name': 'Tag2'}]}

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):

        recipe = create_recipe(user=self.user)
        tag = Tag.objects.create(user=self.user, name='Tag1')

        recipe.tags.add(tag)

        payload = {'tags': []}

        res = self.client.patch(detail_url(recipe.id), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertNotIn(tag, recipe.tags.all())

        self.assertEqual(recipe.tags.count(), 0)

    def create_new_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients"""
        payload = {
            'title': 'Sample update title',
            'time_minutes': 6,
            'price': Decimal('6.25'),
            'ingredients': [{'name': 'Ingredient1'}, {'name': 'Ingredient2'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(
                name=ingredient['name']).exists())

    def create_new_recipe_with_existing_ingredient(self):
        """Test creating recipe with existing tag"""

        ingredient1 = Ingredient.objects.create(name='Ingredient1')

        payload = {
            'title': 'Sample update title',
            'time_minutes': 6,
            'price': Decimal('6.25'),
            'ingredients': [{'name': 'Ingredient1'}, {'name': 'Ingredient2'}]
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.count(), 1)
        self.assertIn(recipe.ingredients.all(), ingredient1)

        for ingredient in payload['ingredients']:
            self.assertTrue(recipe.ingredients.filter(
                name=ingredient['name']).exists())

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when update recipe"""

        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'Ingredient1'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(user=self.user)
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""

        ingredient1 = Ingredient.objects.create(user=self.user,
                                                name='Ingredient1')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user,
                                                name='Ingredient2')

        payload = {'ingredients': [{'name': 'Ingredient2'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingredient = Ingredient.objects.create(user=self.user,
                                               name='Ingredient1')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)
        payload = {'ingredients': []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(ingredient, recipe.ingredients.all())
        self.assertEqual(recipe.ingredients.count(), 0)
