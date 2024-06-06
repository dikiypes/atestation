from rest_framework.test import APIClient, APITestCase

from app_user.models import CustomUser


class BaseTestCase(APITestCase):
    """
    Базовые настройки тест-кейса.
    Создание пользователей.
    Создание клиента для пользователя.
    Аутентификация пользователя.
    """

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

    PRODUCT = {
        "name": "Phone",
        "model": "Samsung A52",
        "release_date": "2023-09-29",
        "supplier": 0
    }

    URL = "/api/suppliers/"
    URL_PRODUCT = "/api/products/"

    @staticmethod
    def create_authenticated_client(user_data):
        client = APIClient()
        login = client.post(
            "/api/users/token/",
            {"email": user_data["email"], "password": user_data["password"]},
        )
        access_token = login.json().get("access")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        return client

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email=self.USER_DATA["email"],
            password=self.USER_DATA["password"],
            first_name=self.USER_DATA["first_name"],
            last_name=self.USER_DATA["last_name"]
        )
        self.user_client = self.create_authenticated_client(self.USER_DATA)
