from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import json


class TestEndpoints(APITestCase):

    def test_publish_ok(self):
        access_token = 'ACCESS_TOKEN'
        summit_id = 2
        url = reverse('entity_updates:create', kwargs={'summit_id': summit_id})

        data = {
            "entity_id": 1,
            "entity_type": "Presentation",
            "entity_operator": "INSERT",
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=access_token),
                                    data, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_publish_412_entity_type(self):
        access_token = 'ACCESS_TOKEN'
        summit_id = 1
        url = reverse('entity_updates:create', kwargs={'summit_id': summit_id})

        data = {
            "entity_id": 1,
            "entity_type": "WRONG",
            "entity_operator": "INSERT",
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=access_token),
                                    data, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)

    def test_publish_412_entity_operator(self):
        access_token = 'ACCESS_TOKEN'
        summit_id = 1
        url = reverse('entity_updates:create', kwargs={'summit_id': summit_id})

        data = {
            "entity_id": 1,
            "entity_type": "Presentation",
            "entity_operator": "WRONG",
        }

        response = self.client.post('{url}?access_token={access_token}'.format(url=url, access_token=access_token),
                                    data, format='json')
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED)
