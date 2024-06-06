from rest_framework import status
from rest_framework.test import APIClient

from app_shop.models import Product
from app_shop.tests.base_test import BaseTestCase


class ProductPartialUpdateAPITestCase(BaseTestCase):
    """Частичное обновление продукта"""

    def setUp(self):
        super().setUp()
        supplier = self.user_client.post(self.URL, self.FACTORY_1_DATA).json()
        supplier_id = supplier['id']

        self.product_data = {
            'name': 'OriginalName',
            'model': 'OriginalModel',
            'release_date': '2022-03-03',
            'supplier': supplier_id
        }
        response = self.user_client.post(self.URL_PRODUCT, self.product_data)
        self.product_to_update = response.json()

    def test_unauthorized_user_cannot_partial_update_product(self):
        """Неавторизованный пользователь не может частично обновлять продукт"""
        update_data = {'name': 'UpdatedName'}
        client = APIClient()
        response = client.patch(f"{self.URL_PRODUCT}{self.product_to_update['id']}/", update_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json().get("detail"), "Учетные данные не были предоставлены.")

    def test_authorized_user_can_partial_update_product(self):
        """Авторизованный пользователь может успешно частично обновить продукт"""

        update_data = {'name': 'UpdatedName'}
        response = self.user_client.patch(f"{self.URL_PRODUCT}{self.product_to_update['id']}/", update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_product = Product.objects.get(id=self.product_to_update['id'])
        self.assertEqual(updated_product.name, 'UpdatedName')

    def test_cannot_partial_update_product_with_blank_or_spaces_fields(self):
        """Нельзя частично обновить продукт с пустыми или состоящими из пробелов полями"""

        self.user_client.post(self.URL_PRODUCT, self.product_data)
        product_to_update = Product.objects.last()

        fields_to_test = ["name", "model"]

        for field in fields_to_test:
            update_data = {field: ""}
            response = self.user_client.patch(f"{self.URL_PRODUCT}{product_to_update.id}/", update_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get(field)[0], 'Это поле не может быть пустым.')

            update_data = {field: "   "}
            response = self.user_client.patch(f"{self.URL_PRODUCT}{product_to_update.id}/", update_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get(field)[0], 'Это поле не может быть пустым.')

    def test_cannot_partial_update_product_with_duplicate_unique_fields(self):
        """Нельзя обновить продукт так, чтобы повторялись уникальные поля"""

        another_product_data = self.product_data.copy()
        another_product_data['name'] = 'another_name'
        another_product = self.user_client.post(self.URL_PRODUCT, another_product_data).json()

        update_data = self.product_data.copy()
        response = self.user_client.patch(f"{self.URL_PRODUCT}{another_product['id']}/", update_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get('non_field_errors')[0],
                         'Поля name, model, release_date, supplier должны производить массив с уникальными значениями.')

    def test_cannot_update_supplier_with_nonexistent_id(self):
        """Нельзя обновить поставщика с несуществующим ID"""

        product_data = self.product_data.copy()
        product_data['name'] = 'another_name'
        another_product = self.user_client.post(self.URL_PRODUCT, product_data).json()

        response = self.user_client.patch(f"{self.URL_PRODUCT}{another_product['id']}/", {'supplier': 99999})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['supplier'][0],
                         'Недопустимый первичный ключ "99999" - объект не существует.')
