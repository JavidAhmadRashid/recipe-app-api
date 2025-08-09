"""
Test cases for the recipe API endpoints.
"""

from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a sample recipe."""
    defaults = {
        'title': 'Sample Recipe',
        'time_minutes': 30,
        'price': Decimal('5.00'),
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    """Create and return a sample user."""
    return get_user_model().objects.create_user(**params)

class PublicRecipeApiTests(TestCase):
    """Test the publicly available recipe API."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth requiredto call api."""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    
class PrivateRecipeApiTests(TestCase):
    """Test the authorized user recipe API."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email = 'user@example.com',
            password = 'testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_recipes_limited_to_user(self):
        """Test retrieving recipes for user."""
        other_user = create_user(
            email='other@example.com',
            password='testpass123'
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test getting recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            'title': 'Chocolate Cheesecake',
            'time_minutes': 60,
            'price': Decimal('4.50'),
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch."""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe Title',
            link=original_link
        )

        payload = {'title': 'Updated Recipe Title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        """Test updating a recipe with put."""
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe Title',
            link='https://example.com/recipe.pdf',
            description='Sample description',
        )

        payload = {
            'title': 'Updated Recipe Title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'Updated description',
            'time_minutes': 45,
            'price': Decimal('3.50'),
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the user results in an error."""
        new_user = create_user(email = 'test@example.com', password='testpass123')
        recipe = create_recipe(user=self.user)
        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

    def test_update_user_returns_error(self):
        """Test changing the user results in an error."""
        new_user = create_user(
            email = 'test@example.com',
            password='testpass123'
        )

        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """Test trying to delete another user's recipe gives error."""
        other_user = create_user(
            email = 'test2@example.com',
            password='testpass123'
        )
        recipe = create_recipe(user=other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
    
    def test_create_recipe_with_new_ingredient(self):
        """Test creating with new ingredient"""
        payload = {
            'title': 'Pizza',
            'time_minutes': 30,
            'price': 60.40,
            'ingredients': [
                {'name':'Pepper'},
                {'name': 'Eggs'}
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipies = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipies.count(), 1)
        recipe = recipies[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user,
            ).exists
            self.assertTrue(exists)

    def test_create_recipe_with_new_tag(self):
        """Test Creating a recipe with a new tag."""
        payload = {
            'title':'Thai Praown Curry',
            'time_minutes': 30, 
            'price': 40.50,
            'tags':[{'name':'Thai'}, {'name':'Dinner'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipies = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipies.count(), 1)
        recipe = recipies[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user,
            ).exists
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating recipe with exicting Ingredient."""
        ingredient = Ingredient.objects.create(user = self.user, name = 'Vanilla')
        payload = {
            'title': 'Recipe new',
            'time_minutes': 14,
            'price': 44.4,
            'ingredients': [
                {'name': 'Ingredient 1'},
                {'name': 'Vanilla'},
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipies = Recipe.objects.filter(user= self.user)
        self.assertEqual(recipies.count(), 1)
        recipe = recipies[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user
            ).exists
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test Creating Recipe with existing Tag."""
        tag_indian = Tag.objects.create(user = self.user, name = 'Indian')
        payload = {
            'title':'Pongal',
            'time_minutes': 16,
            'price': 4.5,
            'tags': [
                {'name':'Indian'},
                {'name': 'Breakfast'}
            ]
        }
        res = self.client.post(RECIPE_URL, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipies = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipies.count(), 1)
        recipe = recipies[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)
        
    def test_create_tag_on_update(self):
        """Test Creating tag when updating a recipe."""
        recipe = create_recipe(user = self.user)

        payload = {
            'tags':[
                {'name': 'Launch'},
            ]
        }
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user = self.user, name ='Launch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_updatae_recipe_assign_tag(self):
        """Test assginig an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user = self.user, name = 'Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user= self.user, name = 'Lunch')
        payload = {'tags': [
            {'name':'Lunch'}
        ]}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format = 'json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing recipe tags."""
        tag = Tag.objects.create(user = self.user, name = 'Dessert')
        recipe = create_recipe(user = self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
    
