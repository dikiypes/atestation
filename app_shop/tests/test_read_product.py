from rest_framework import status
from rest_framework.test import APIClient

from app_shop.tests.base_test import BaseTestCase


class ProductReadAPITestCase(BaseTestCase):
    """Чтение продукта"""

    def setUp(self):
        super().setUp()

        supplier = self.user_client.post(self.URL, self.FACTORY_1_DATA).json()
        supplier_id = supplier['id']

        self.product_data_1 = {
            'name': 'Product1',
            'model': 'Model1',
            'release_date': '2022-01-01',
            'supplier': supplier_id
        }
        response = self.user_client.post(self.URL_PRODUCT, self.product_data_1)
        self.product1 = response.json()

        self.product_data_2 = {
            'name': 'Product2',
            'model': 'Model2',
            'release_date': '2022-02-02',
            'supplier': supplier_id
        }
        response = self.user_client.post(self.URL_PRODUCT, self.product_data_2)
        self.product2 = response.json()

    def test_unauthorized_user_cannot_read_products(self):
        """Неавторизованный пользователь не может просмотреть список продуктов"""
        client = APIClient()
        response = client.get(f"{self.URL_PRODUCT}{self.product1['id']}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json().get("detail"), "Учетные данные не были предоставлены.")

    def test_unauthorized_user_cannot_read_product_detail(self):
        """Неавторизованный пользователь не может просмотреть детали продукта"""
        client = APIClient()
        response = client.get(self.URL_PRODUCT)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json().get("detail"), "Учетные данные не были предоставлены.")

    def test_authorized_user_can_read_product_list(self):
        """Авторизованный пользователь может просмотреть список продуктов"""
        response = self.user_client.get(self.URL_PRODUCT)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_non_existent_product(self):
        """При запросе продукта с несуществующим ID должна возвращаться ошибка"""
        response = self.user_client.get(f"{self.URL_PRODUCT}999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authorized_user_can_read_single_product(self):
        """Авторизованный пользователь может просмотреть детали продукта"""
        response = self.user_client.get(f"{self.URL_PRODUCT}{self.product1['id']}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["name"], self.product_data_1["name"])
        self.assertEqual(response.data["model"], self.product_data_1["model"])
        self.assertEqual(response.data["release_date"], self.product_data_1["release_date"])
        self.assertEqual(response.data["supplier"], self.product_data_1["supplier"])
