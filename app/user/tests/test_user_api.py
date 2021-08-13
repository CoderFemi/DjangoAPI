from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)  # type:ignore


class PublicUserApiTests(TestCase):
    '''Test the users API (public)'''

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        '''Test creating user with valid payload is successful'''
        payload = {
            'email': 'test@email.com',
            'password': 'pass1234',
            'name': 'Test Name',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)  # type:ignore
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)  # type:ignore

    def test_user_exists(self):
        '''Test creating user that already exists fails'''
        payload = {
            'email': 'test@email.com',
            'password': 'pass1234',
            'name': 'Test Name',
        }
        # The double asterisks passes in the dict fields in 'payload' as kwargs
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        '''Test that the password is not less than 8 characters'''
        payload = {
            'email': 'test@email.com',
            'password': 'ps',
            'name': 'Test Name',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model().objects.filter(email=payload['email']).exists()
        )  # type:ignore
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        '''Test that a token is created for the user'''
        payload = {
            'email': 'test@email.com',
            'password': 'pass1234',
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)  # type:ignore
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_with_invalid_credentials(self):
        '''Test that token is not created if invalid credentials supplied'''
        payload_one = {
            'email': 'test@email.com',
            'password': 'pass1234',
        }
        payload_two = {
            'email': 'test@email.com',
            'password': 'wrongpassword',
        }
        create_user(**payload_one)
        res = self.client.post(TOKEN_URL, payload_two)
        self.assertNotIn('token', res.data)  # type:ignore
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        '''Test that token is not created if user doesn't exist'''
        payload = {
            'email': 'test@email.com',
            'password': 'pass1234',
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)  # type:ignore
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        '''Test that email and password are required'''
        payload = {
            'email': 'one',
            'password': '',
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', res.data)  # type:ignore
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
