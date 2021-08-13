from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models  # type: ignore


def sample_user(email='test@email.com', password='pass1234'):
    '''Create a sample user'''
    user_objects = get_user_model().objects
    return user_objects.create_user(email, password)  # type:ignore


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = 'johnson@test.com'
        password = 'pass1234'
        user = get_user_model().objects.create_user(  # type:ignore
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = 'test@RECIPEAPP.com'
        user = get_user_model().objects.create_user(email, 'test123')  # type: ignore
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        '''Test creating user with no email raises error'''
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')  # type: ignore

    def test_new_superuser(self):
        '''Test creating a new superuser'''
        user = get_user_model().objects.create_superuser(  # type: ignore
            'test@recipeapp.com', 'pass123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        '''Test the tag string representation'''
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Keto',
        )

        self.assertEqual(str(tag), tag.name)
