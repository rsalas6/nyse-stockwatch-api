from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Company


class CompanyAPITest(APITestCase):
    def setUp(self):
        self.url = reverse("company-list-create")

    def test_create_company_valid(self):
        valid_data = {
            "name": "Valid Company",
            "symbol": "AAPL",
            "description": "The iPhone company",
        }
        response = self.client.post(self.url, valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Company.objects.get().symbol, "AAPL")

    def test_create_company_invalid(self):
        invalid_data = {"name": "Invalid Company", "symbol": "LOL"}
        response = self.client.post(self.url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        self.assertEqual(Company.objects.count(), 0)
