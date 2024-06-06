from rest_framework import status
from rest_framework.test import APIClient

from app_shop.models import Supplier
from app_shop.tests.base_test import BaseTestCase


class SupplierCreateAPITestCase(BaseTestCase):
    """Создание звена"""

    def test_unauthorized_user_cannot_create_supplier(self):
        """Неавторизованный пользователь не может создать звено"""
        client = APIClient()
        response = client.post(self.URL, self.FACTORY_1_DATA)
        response_data = response.json()

        self.assertEqual(response_data.get("detail"), "Учетные данные не были предоставлены.")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_supplier_with_blank_or_spaces_fields(self):
        """Нельзя создать звено с пустыми или состоящими из пробелов полями"""

        fields_to_test = ["name", "country", "city", "street", "house_number"]

        for field in fields_to_test:
            data = self.FACTORY_1_DATA.copy()

            data[field] = ""
            response = self.user_client.post(self.URL, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get(field)[0], 'Это поле не может быть пустым.')

            data[field] = "   "
            response = self.user_client.post(self.URL, data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get(field)[0], 'Это поле не может быть пустым.')

    def test_cannot_create_supplier_with_negative_debt(self):
        """Нельзя создать звено с отрицательным значением debt"""

        data = self.FACTORY_1_DATA.copy()
        data["debt"] = "-1500.80"

        response = self.user_client.post(self.URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get('debt')[0], 'Убедитесь, что это значение больше либо равно 0.')

    def test_supplier_unique_constraints(self):
        """Поставщик с одинаковой комбинацией 'country', 'city', 'name', 'email' не может быть создан"""

        response_1 = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)

        response_2 = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_2.json().get('non_field_errors')[0],
                         'Поля country, city, name, email должны производить массив с уникальными значениями.')

    def test_authorized_user_can_create_suppliers(self):
        """Можно создать разные типы поставщиков без родителя и без долга"""
        supplier_data_list = [self.FACTORY_1_DATA, self.RETAIL_DATA, self.ENT_DATA]

        for data in supplier_data_list:
            response = self.user_client.post(self.URL, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            supplier_type = data["type_supplier"]
            self.assertTrue(Supplier.objects.filter(type_supplier=supplier_type).exists())

        self.assertEqual(Supplier.objects.count(), len(supplier_data_list))

    def test_factory_cannot_have_parent(self):
        """Завод не может иметь родителя"""

        response_1 = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        factory_1_id = response_1.json()['id']

        factory_2_data = self.FACTORY_2_DATA.copy()
        factory_2_data['parent'] = factory_1_id

        response_2 = self.user_client.post(self.URL, factory_2_data)

        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_2.json().get('non_field_errors')[0], 'Ошибка: завод не может иметь родителя')

    def test_factory_cannot_have_debt(self):
        """Завод не может иметь долг"""

        data = self.FACTORY_1_DATA.copy()
        data["debt"] = "1000.00"

        response = self.user_client.post(self.URL, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get('non_field_errors')[0], 'Ошибка: у звена без родителя не может быть долга')

    def test_cannot_create_supplier_without_parent_with_debt(self):
        """Нельзя создать звено без родителя с долгом"""

        supplier_data_list = [
            self.FACTORY_1_DATA,
            self.RETAIL_DATA,
            self.ENT_DATA
        ]

        for data in supplier_data_list:
            data_with_debt = data.copy()
            data_with_debt["debt"] = 1500.80
            response = self.user_client.post(self.URL, data_with_debt)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.json().get("non_field_errors")[0],
                             "Ошибка: у звена без родителя не может быть долга")

    def test_can_create_supplier_with_parent_without_debt(self):
        """Создание звена с родителем и без долга"""

        response_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        self.assertEqual(response_parent.status_code, status.HTTP_201_CREATED)
        parent_id = response_parent.json()['id']

        supplier_data_list = [self.RETAIL_DATA, self.ENT_DATA]

        for data in supplier_data_list:
            data_with_parent = data.copy()
            data_with_parent["parent"] = parent_id

            response = self.user_client.post(self.URL, data_with_parent)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            supplier_id = response.json()['id']
            supplier = Supplier.objects.get(id=supplier_id)
            self.assertEqual(supplier.parent.id, parent_id)

    def test_can_create_supplier_with_parent_with_debt(self):
        """Создание звена с родителем и с долгом"""

        response_parent = self.user_client.post(self.URL, self.FACTORY_1_DATA)
        self.assertEqual(response_parent.status_code, status.HTTP_201_CREATED)
        parent_id = response_parent.json()['id']

        supplier_data_list = [self.RETAIL_DATA, self.ENT_DATA]

        for data in supplier_data_list:
            data_with_parent_and_debt = data.copy()
            data_with_parent_and_debt["parent"] = parent_id
            data_with_parent_and_debt["debt"] = 500.00

            response = self.user_client.post(self.URL, data_with_parent_and_debt)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            supplier_id = response.json()['id']
            supplier = Supplier.objects.get(id=supplier_id)
            self.assertEqual(supplier.parent.id, parent_id)
            self.assertEqual(supplier.debt, 500.00)

    def test_invalid_type_supplier(self):
        """Проверка недопустимых значений для типа поставщика (type_supplier)"""
        invalid_data = self.FACTORY_1_DATA.copy()
        invalid_data["type_supplier"] = "invalid_type"

        response = self.user_client.post(self.URL, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get('type_supplier')[0],
                         f'Значения {invalid_data["type_supplier"]} нет среди допустимых вариантов.')

    def test_create_supplier_with_non_existent_parent(self):
        """Проверка создания звена с несуществующим родителем"""
        data_with_non_existent_parent = self.RETAIL_DATA.copy()
        data_with_non_existent_parent['parent'] = 9999

        response = self.user_client.post(self.URL, data_with_non_existent_parent)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get('parent')[0],
                         f'Недопустимый первичный ключ "{data_with_non_existent_parent["parent"]}" - '
                         f'объект не существует.')
