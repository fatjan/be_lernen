from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from api.models import Exercise, Language
from unittest.mock import patch

class ExerciseViewSetTests(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test language
        self.language = Language.objects.create(
            code='de',
            name='German'
        )
        
        # Create test exercise
        self.exercise = Exercise.objects.create(
            title='Test Exercise',
            language=self.language,
            exercise_type='reading',
            difficulty_level='A1',
            content='Test content',
            instructions='Test instructions'
        )

    @patch('api.views.exercise.ExerciseGenerator')
    def test_generate_exercise_reading(self, mock_generator):
        # Mock the generator response
        mock_generator.return_value.generate_reading_exercise.return_value = {
            'title': 'Test Exercise',
            'content': 'Test content',
            'questions': [],
            'language': self.language,
            'exercise_type': 'reading',
            'difficulty_level': 'A1'
        }

        url = reverse('exercise-generate')
        data = {
            'type': 'reading',
            'language': 'de',
            'level': 'A1',
            'topic': 'daily routine'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('title', response.data)
        self.assertIn('content', response.data)
        self.assertIn('questions', response.data)

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)
        url = reverse('exercise-generate')
        response = self.client.post(url, {}, format='json')
        # Update expected status code to 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)