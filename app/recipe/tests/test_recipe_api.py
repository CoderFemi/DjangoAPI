from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer


RECIPES_URL = reverse('recipe:recipe-list')


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
