from rest_framework import status
from rest_framework.test import APIClient

from app_shop.models import Product
from app_shop.tests.base_test import BaseTestCase


class ProductCreateAPITestCase(BaseTestCase):
    """Создание продукта"""

    def setUp(self):
        super().setUp()

        supplier = self.user_client.post(self.URL, self.FACTORY_1_DATA).json()
        supplier_id = supplier['id']

        self.product_data = self.PRODUCT
        self.product_data['supplier'] = supplier_id

    def test_unauthorized_user_cannot_create_product(self):
        """Неавторизованный пользователь не может создать продукт"""

        client = APIClient()
        response = client.post(self.URL_PRODUCT, self.product_data)
        response_data = response.json()

        self.assertEqual(response_data.get("detail"), "Учетные данные не были предоставлены.")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_product_with_blank_or_spaces_fields(self):
        """Нельзя создать продукт с пустыми или состоящими из пробелов полями"""

        fields_to_test = ["name", "model"]

        for field in fields_to_test:
            data = self.product_data.copy()

            data[field] = ""
            response = self.user_client.post(self.URL_PRODUCT, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get(field)[0], 'Это поле не может быть пустым.')

            data[field] = "   "
            response = self.user_client.post(self.URL_PRODUCT, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get(field)[0], 'Это поле не может быть пустым.')

    def test_product_unique_constraints(self):
        """Продукт с одинаковой комбинацией 'name', 'model', 'release_date', 'supplier' не может быть создан"""

        response_1 = self.user_client.post(self.URL_PRODUCT, self.product_data)
        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)

        response_2 = self.user_client.post(self.URL_PRODUCT, self.product_data)
        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_2.json().get('non_field_errors')[0],
                         'Поля name, model, release_date, supplier должны производить массив с уникальными значениями.')

    def test_authorized_user_can_create_product(self):
        """Успешное создание продукта"""

        response = self.user_client.post(self.URL_PRODUCT, self.product_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)

    def test_non_existent_supplier(self):
        """Нельзя создать продукт, если поставщик не существует"""

        data = self.product_data.copy()
        data['supplier'] = 999999
        response = self.user_client.post(self.URL_PRODUCT, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['supplier'][0],
                         f'Недопустимый первичный ключ "{data["supplier"]}" - объект не существует.')

    def test_missing_required_fields(self):
        """Нельзя создать продукт без обязательных полей"""

        required_fields = ['name', 'model', 'release_date', 'supplier']
        for field in required_fields:
            data = self.product_data.copy()
            del data[field]
            response = self.user_client.post(self.URL_PRODUCT, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
