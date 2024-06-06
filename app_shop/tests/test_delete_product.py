from rest_framework import status
from rest_framework.test import APIClient

from app_shop.tests.base_test import BaseTestCase


class ProductDeleteAPITestCase(BaseTestCase):
    """Удаление продукта"""

    def setUp(self):
        super().setUp()

        supplier = self.user_client.post(self.URL, self.FACTORY_1_DATA).json()
        supplier_id = supplier['id']

        self.product_data = {
            'name': 'ProductToDelete',
            'model': 'ModelToDelete',
            'release_date': '2022-03-03',
            'supplier': supplier_id
        }
        response = self.user_client.post(self.URL_PRODUCT, self.product_data)
        self.product_to_delete = response.json()

    def test_unauthorized_user_cannot_delete_product(self):
        """Неавторизованный пользователь не может удалять продукт"""
        client = APIClient()
        response = client.delete(f"{self.URL_PRODUCT}{self.product_to_delete['id']}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json().get("detail"), "Учетные данные не были предоставлены.")

    def test_authorized_user_can_delete_product(self):
        """Авторизованный пользователь может успешно удалить продукт"""
        response = self.user_client.delete(f"{self.URL_PRODUCT}{self.product_to_delete['id']}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.user_client.get(f"{self.URL_PRODUCT}{self.product_to_delete['id']}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
