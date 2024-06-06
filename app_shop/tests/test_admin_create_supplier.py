from django.test import TestCase, Client
from django.urls import reverse

from app_shop.models import Supplier
from app_user.models import CustomUser


class BaseAdminTestCase(TestCase):
    USER_DATA = {
        "email": "ivan@mail.ru",
        "password": "qwerty123!",
        "password2": "qwerty123!",
        "first_name": "Ivan",
        "last_name": "Ivanov",
    }

    FACTORY_1_DATA = {
        "type_supplier": "factory",
        "name": "Прогресс",
        "email": "factory_1@example.com",
        "country": "Россия",
        "city": "Москва",
        "street": "Ленина",
        "house_number": "1",
        "debt": 0
    }

    FACTORY_2_DATA = {
        "type_supplier": "factory",
        "name": "Успешный завод",
        "email": "factory_2@example.com",
        "country": "Россия",
        "city": "Санкт-Петербург",
        "street": "Таврическая",
        "house_number": "5",
        "debt": 0
    }

    RETAIL_DATA = {
        "type_supplier": "retail",
        "name": "Успех",
        "email": "success_retail@example.com",
        "country": "Беларусь",
        "city": "Минск",
        "street": "Пушкина",
        "house_number": "1",
        "debt": 0,
    }

    ENT_DATA = {
        "type_supplier": "entrepreneur",
        "name": "Иванов И.П.",
        "email": "ivanov_@example.com",
        "country": "Россия",
        "city": "Нижний Новгород",
        "street": "Проспект Гагарина",
        "house_number": "10",
        "debt": 0
    }
    SUPPLIER_WITHOUT_DEBT = {
        "type_supplier": "retail",
        "name": "retail_without_debt_and_children",
        "email": "retail_without_debt_and_children@example.com",
        "country": "Беларусь",
        "city": "Минск",
        "street": "Пушкина",
        "house_number": "10",
        "debt": 0,
    }
    SUPPLIER_WITH_DEBT = {
        "type_supplier": "retail",
        "name": "retail_with_debt",
        "email": "retail_with_debt@example.com",
        "country": "Россия",
        "city": "Новосибирск",
        "street": "Пушкина",
        "house_number": "2",
        "debt": 1000
    }

    @staticmethod
    def create_authenticated_admin_client(admin_data):
        client = Client()
        client.login(username=admin_data["email"], password=admin_data["password"])
        return client

    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            email=self.USER_DATA["email"],
            password=self.USER_DATA["password"],
            first_name=self.USER_DATA["first_name"],
            last_name=self.USER_DATA["last_name"]
        )
        self.admin_client = self.create_authenticated_admin_client(self.USER_DATA)


class SupplierCreateAdminTestCase(BaseAdminTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('admin:app_shop_supplier_add')

    def test_admin_unauthorized_user_cannot_create_product(self):
        """Неавторизованный пользователь не может создать продукт через админ-панель"""

        client = Client()
        response = client.post(self.url, self.FACTORY_1_DATA)

        login_url = reverse('admin:login') + "?next=" + self.url
        self.assertRedirects(response, login_url)
        self.assertEqual(response.status_code, 302)

    def test_admin_cannot_create_supplier_with_blank_or_spaces_fields(self):
        """Нельзя создать звено с пустыми или состоящими из пробелов полями через админ-панель"""

        fields_to_test = ["name", "country", "city", "street", "house_number"]

        for field in fields_to_test:
            data = self.FACTORY_1_DATA.copy()

            data[field] = ""
            response = self.admin_client.post(self.url, data)
            self.assertContains(response, 'Обязательное поле.')

            data[field] = "   "
            response = self.admin_client.post(self.url, data)
            self.assertContains(response, 'Обязательное поле.')

    def test_admin_cannot_create_supplier_with_negative_debt(self):
        """Нельзя создать звено с отрицательным значением debt через админ-панель"""

        data = self.FACTORY_1_DATA.copy()
        data["debt"] = "-1500.80"

        response = self.admin_client.post(self.url, data)
        self.assertContains(response, 'Убедитесь, что это значение больше либо равно 0.')

    def test_admin_supplier_unique_constraints(self):
        """
        Поставщик с одинаковой комбинацией 'country', 'city', 'name', 'email'
        не может быть создан через админ-панель
        """

        response_1 = self.admin_client.post(self.url, self.FACTORY_1_DATA)
        self.assertEqual(response_1.status_code, 302)

        response_2 = self.admin_client.post(self.url, self.FACTORY_1_DATA)
        self.assertContains(response_2,
                            'Звено сети с такими значениями полей Страна, Город, Название и Электронная почта '
                            'уже существует.')

    def test_admin_authorized_user_can_create_suppliers(self):
        """Можно создать разные типы поставщиков без родителя и без долга через админ-панель"""
        supplier_data_list = [self.FACTORY_1_DATA, self.RETAIL_DATA, self.ENT_DATA]

        for data in supplier_data_list:
            response = self.admin_client.post(self.url, data)
            self.assertEqual(response.status_code, 302)
            supplier_type = data["type_supplier"]

            self.assertTrue(Supplier.objects.filter(type_supplier=supplier_type).exists())

        self.assertEqual(Supplier.objects.count(), len(supplier_data_list))

    def test_admin_factory_cannot_have_parent(self):
        """Завод не может иметь родителя через админ-панель"""

        response_1 = self.admin_client.post(self.url, self.FACTORY_1_DATA)
        self.assertEqual(response_1.status_code, 302)

        created_factory = Supplier.objects.get(name=self.FACTORY_1_DATA["name"])
        factory_2_data = self.FACTORY_2_DATA.copy()
        factory_2_data['parent'] = created_factory.id
        response_2 = self.admin_client.post(self.url, factory_2_data)
        self.assertContains(response_2, 'Ошибка: завод не может иметь родителя')

    def test_admin_factory_cannot_have_debt(self):
        """Завод не может иметь долг через админ-панель"""

        data = self.FACTORY_1_DATA.copy()
        data["debt"] = "1000.00"

        response = self.admin_client.post(self.url, data)
        self.assertContains(response, 'Ошибка: у звена без родителя не может быть долга')

    def test_admin_cannot_create_supplier_without_parent_with_debt(self):
        """Нельзя создать звено без родителя с долгом через админ-панель"""

        supplier_data_list = [
            self.FACTORY_1_DATA,
            self.RETAIL_DATA,
            self.ENT_DATA
        ]

        for data in supplier_data_list:
            data_with_debt = data.copy()
            data_with_debt["debt"] = 1500.80
            response = self.admin_client.post(self.url, data_with_debt)

            self.assertContains(response, "Ошибка: у звена без родителя не может быть долга")

    def test_admin_can_create_supplier_with_parent_without_debt(self):
        """Создание звена с родителем и без долга через админ-панель"""

        response_parent = self.admin_client.post(self.url, self.FACTORY_1_DATA)
        self.assertEqual(response_parent.status_code, 302)

        parent_id = Supplier.objects.latest('id').id
        supplier_data_list = [self.RETAIL_DATA, self.ENT_DATA]

        for data in supplier_data_list:
            data_with_parent = data.copy()
            data_with_parent["parent"] = parent_id

            response = self.admin_client.post(self.url, data_with_parent)
            self.assertEqual(response.status_code, 302)

            supplier_id = Supplier.objects.latest('id').id
            supplier = Supplier.objects.get(id=supplier_id)
            self.assertEqual(supplier.parent.id, parent_id)

    def test_admin_can_create_supplier_with_parent_with_debt(self):
        """Создание звена с родителем и с долгом через админ-панель"""

        response_parent = self.admin_client.post(self.url, self.FACTORY_1_DATA)
        self.assertEqual(response_parent.status_code, 302)

        parent_id = Supplier.objects.latest('id').id

        supplier_data_list = [self.RETAIL_DATA, self.ENT_DATA]

        for data in supplier_data_list:
            data_with_parent_and_debt = data.copy()
            data_with_parent_and_debt["parent"] = parent_id
            data_with_parent_and_debt["debt"] = 500.00

            response = self.admin_client.post(self.url, data_with_parent_and_debt)

            self.assertEqual(response.status_code, 302)

            supplier_id = Supplier.objects.latest('id').id
            supplier = Supplier.objects.get(id=supplier_id)
            self.assertEqual(supplier.parent.id, parent_id)
            self.assertEqual(supplier.debt, 500.00)
