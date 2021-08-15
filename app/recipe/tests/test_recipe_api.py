import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')  # URL name portion auto-created by router


def image_upload_url(recipe_id):
    '''Return URL for recipe image upload'''
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    '''Return recipe detail URL'''
    return reverse(
        'recipe:recipe-detail', args=[recipe_id]
    )  # URL name portion auto-created by router


def sample_tag(user, name='Dessert'):
    '''Create and return a sample tag'''
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Garlic'):
    '''Crate and return a sample ingredient'''
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    '''Create and return a sample recipe'''
    defaults = {'title': 'Sample recipe', 'time_minutes': 10, 'price': 350.00}

    # "|=" operator can also be used to update the dict
    # i.e. defaults |= params
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    '''Test unauthenticated recipe API access'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test that authentication is required'''
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    '''Test unauthenticated recipe API Access'''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('test@email.com', 'pass1234')  # type: ignore
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        '''Test retrieving a list of recipes'''
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)  # type:ignore
        self.assertEqual(res.data, serializer.data)  # type: ignore

    def test_recipes_limited_to_user(self):
        '''Test retrieving recipes is limited to authenticated user'''
        user_two = get_user_model().objects.create_user('another@email.com', 'pass1234')  # type: ignore
        sample_recipe(user=user_two)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # type:ignore
        self.assertEqual(res.data, serializer.data)  # type:ignore

    def test_view_recipe_detail(self):
        '''Test viewing a recipe detail'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)  # type:ignore

    def test_create_basic_recipe(self):
        '''Test creating recipe'''
        payload = {'title': 'Carribean stew', 'time_minutes': 45, 'price': 420.00}
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])  # type:ignore
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        '''Test creating a recipe with tags'''
        tag_one = sample_tag(user=self.user, name='Vegan')
        tag_two = sample_tag(user=self.user, name='Starter')
        payload = {
            'title': "Sweet cheesecake",
            'tags': [tag_one.id, tag_two.id],
            'time_minutes': 60,
            'price': 20.00,
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])  # type:ignore
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag_one, tags)
        self.assertIn(tag_two, tags)

    def test_create_recipe_with_ingredients(self):
        '''Test creating a recipe with ingredients'''
        ingredient_one = sample_ingredient(user=self.user, name='Chicken')
        ingredient_two = sample_ingredient(user=self.user, name='Cheese')
        payload = {
            'title': "Chicken Parmesan",
            'ingredients': [ingredient_one.id, ingredient_two.id],
            'time_minutes': 40,
            'price': 70.00,
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])  # type:ignore
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_one, ingredients)
        self.assertIn(ingredient_two, ingredients)

    def test_partial_update_recipe(self):
        '''Test updating a recipe with patch'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='European')

        payload = {'title': 'Fried Rice', 'tags': [new_tag.id]}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        '''Test updating a recipe with put'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {'title': 'Basmati Rice', 'time_minutes': 65, 'price': 25.00}
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('test@email.com', 'pass1234')  # type: ignore
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        '''Test uploading an email to recipe'''
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        '''Test uploading an invalid image'''
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
