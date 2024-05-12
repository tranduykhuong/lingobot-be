from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from history.models import ParaphraseHistory

User = get_user_model()


class ParaphraseHistoryViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        self.base_url = '/api/v1/paraphrase-history/'
        self.valid_payload = {
            'modelType': 'some_model',
            'textStyle': 'some_style',
            'input': 'Some input text',
            'output': {'paraphrased_text': 'Some paraphrased text'}
        }

    def test_list_paraphrase_history(self):
        ParaphraseHistory.objects.create(
            user=self.user,
            model_type='some_model',
            text_style='some_style',
            input='Some input text',
            output={'paraphrased_text': 'Some paraphrased text'}
        )
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_paraphrase_history(self):
        response = self.client.post(self.base_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ParaphraseHistory.objects.count(), 1)
        self.assertEqual(ParaphraseHistory.objects.get().user, self.user)
