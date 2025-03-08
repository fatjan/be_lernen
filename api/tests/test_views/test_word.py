from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from api.models import Word, Language, UserProfile
from api.serializers import WordSerializer

class WordViewSetTests(APITestCase):
    def setUp(self):
        # Create test user (UserProfile will be created automatically via signal)
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Get the automatically created profile instead of creating a new one
        self.profile = self.user.userprofile
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test language
        self.language = Language.objects.create(
            code='de',
            name='German'
        )
        
        # Create test word
        self.word = Word.objects.create(
            word='Haus',
            translation='house',
            language=self.language,
            user=self.user,
            part_of_speech='noun',
            difficulty_level='A1'
        )

    def test_list_words(self):
        url = reverse('word-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_word(self):
        url = reverse('word-list')
        data = {
            'word': 'Katze',
            'translation': 'cat',
            'language': self.language.id,
            'part_of_speech': 'noun',
            'difficulty_level': 'A1',
            'user': self.user.id
        }
        # Add TokenAuthentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.auth_token.key}')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Word.objects.count(), 2)
        self.assertEqual(Word.objects.get(word='Katze').translation, 'cat')

    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Create auth token for the user
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)
        
        self.profile = self.user.userprofile
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test language
        self.language = Language.objects.create(
            code='de',
            name='German'
        )
        
        # Create test word
        self.word = Word.objects.create(
            word='Haus',
            translation='house',
            language=self.language,
            user=self.user,
            part_of_speech='noun',
            difficulty_level='A1'
        )

    def test_list_words(self):
        url = reverse('word-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_word(self):
        url = reverse('word-list')
        data = {
            'word': 'Katze',
            'translation': 'cat',
            'language': self.language.id,
            'part_of_speech': 'noun',
            'difficulty_level': 'easy',
            'user': self.user.id  # Add the user field
        }
        response = self.client.post(url, data, format='json')
        print('ini response', response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Word.objects.count(), 2)
        self.assertEqual(Word.objects.get(word='Katze').translation, 'cat')

    def test_retrieve_word(self):
        url = reverse('word-detail', kwargs={'pk': self.word.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['word'], 'Haus')

    def test_update_word(self):
        url = reverse('word-detail', kwargs={'pk': self.word.pk})
        data = {
            'word': 'Haus',
            'translation': 'home',  # Changed translation
            'language': self.language.id,
            'part_of_speech': 'noun',
            'difficulty_level': 'A1',
            'user': self.user.id  # Add the user field
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Word.objects.get(pk=self.word.pk).translation, 'home')

    def test_delete_word(self):
        url = reverse('word-detail', kwargs={'pk': self.word.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Word.objects.count(), 0)

    def test_batch_create_words(self):
        url = reverse('word-batch')
        data = [
            {
                'word': 'Hund',
                'translation': 'dog',
                'language': self.language.id,
                'part_of_speech': 'noun'
            },
            {
                'word': 'Katze',
                'translation': 'cat',
                'language': self.language.id,
                'part_of_speech': 'noun'
            }
        ]
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Word.objects.count(), 3)  # Including the one from setUp

    def test_word_suggestions(self):
        url = reverse('word-suggestions')
        response = self.client.get(url, {'query': 'Hau', 'language': 'de'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['word'], 'Haus')

    def test_unauthorized_access(self):
        self.client.credentials()  # Clear credentials
        url = reverse('word-list')
        response = self.client.get(url)
        # Update to match the actual response from TokenAuthentication
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_word_filtering(self):
        url = reverse('word-list')
        response = self.client.get(url, {'language': self.language.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_word_search(self):
        url = reverse('word-list')
        response = self.client.get(url, {'search': 'Haus'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)