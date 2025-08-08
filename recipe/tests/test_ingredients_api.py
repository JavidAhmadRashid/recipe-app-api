"""
Tests for the ingredients API in the recipe application.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from recipe.serializers import TagSerializer, IngredientSerializer

from core.models import Tag, Ingredient, Recipe

INGREDIENT_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
    """Create and return a tag detail url"""
    return reverse('recipe:tag-detail', args=[ingredient_id])

def create_user(email = 'test@example.com', password = 'testpass123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    """Test unauthenticated tags API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the tags API."""
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test authenticated tags API access."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of tags."""
        Ingredient.objects.create(user=self.user, name='Lime')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that tags returned are for the authenticated user."""
        other_user = create_user(email='user2@example.com', password='testpass456')
        Ingredient.objects.create(user=other_user, name='Lemon')
        ingredient = Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENT_URL)
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating ingredient's model."""
        ingredient = Ingredient.objects.create(user=self.user, name='after dinner')

        payload = {'name': 'Vanila'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting ingredient by id."""
        ingredient = Ingredient.objects.create(user = self.user, name = 'Lemon-Vanila')

        url = detail_url(ingredient.id)

        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user = self.user)
        self.assertFalse(ingredients.exists())

