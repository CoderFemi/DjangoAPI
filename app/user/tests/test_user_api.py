from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


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
        details = {
            'email': 'test@email.com',
            'password': 'pass1234',
        }
        payload = {
            'email': 'test@email.com',
            'password': 'wrongpassword',
        }
        create_user(**details)
        res = self.client.post(TOKEN_URL, payload)
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

    def test_retrieve_user_unauthorised(self):
        '''Authentication is required for users'''
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    '''Test API requests that require authentication'''

    def setUp(self):
        user_details = {
            'email': 'test@email.com',
            'password': 'pass1234',
            'name': 'Test Name',
        }
        self.user = create_user(**user_details)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_successful(self):
        '''Test retrieving profile for logged in user'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,  # type:ignore
            {
                'name': self.user.name,
                'email': self.user.email,
            },
        )

    def test_post_me_not_allowed(self):
        '''Test that POST is not allowed on the me url'''
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        '''Test updating the user profile for authenticated user'''
        payload = {
            'name': 'New Name',
            'password': 'newpass5678',
        }
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
