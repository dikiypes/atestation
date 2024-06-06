from rest_framework import status
from rest_framework.test import APITestCase

from app_user.models import CustomUser


class UserCreationTestCase(APITestCase):
    """Регистрация пользователя"""

    def setUp(self):
        self.register_url = "/api/users/register/"
        self.valid_user_data = {
            "email": "ivan@mail.com",
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "password": "qwerty123!",
            "password2": "qwerty123!",
        }

    def test_user_can_register(self):
        """Регистрация пользователя с валидными данными"""
        response = self.client.post(
            self.register_url, self.valid_user_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_data = response.json()
        self.assertEqual(
            response_data.get("first_name"), self.valid_user_data.get("first_name")
        )
        self.assertEqual(
            response_data.get("last_name"), self.valid_user_data.get("last_name")
        )
        self.assertIsNone(response_data.get("password"))
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_password_length_less_than_eight(self):
        """Регистрация пользователя с паролем менее восьми символов"""
        short_password_data = self.valid_user_data.copy()
        short_password_data["password"] = "qwe12!"
        short_password_data["password2"] = "qwe12!"

        response = self.client.post(
            self.register_url, short_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_password_without_digits(self):
        """Регистрация пользователя с паролем без цифр"""
        no_digit_password_data = self.valid_user_data.copy()
        no_digit_password_data["password"] = "qweASD!!"
        no_digit_password_data["password2"] = "qweASD!!"

        response = self.client.post(
            self.register_url, no_digit_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_password_without_letters(self):
        """Регистрация пользователя с паролем без букв"""
        no_letter_password_data = self.valid_user_data.copy()
        no_letter_password_data["password"] = "12345678!"
        no_letter_password_data["password2"] = "12345678!"

        response = self.client.post(
            self.register_url, no_letter_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_passwords_do_not_match(self):
        """Регистрация пользователя, когда пароли не совпадают"""
        mismatched_password_data = self.valid_user_data.copy()
        mismatched_password_data["password2"] = "differentpassword"

        response = self.client.post(
            self.register_url, mismatched_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_invalid_names(self):
        """Имя и фамилия не могут быть пустыми или состоять только из пробелов."""

        invalid_name_data_list = [
            {"first_name": "", "last_name": "ValidLast"},
            {"first_name": "  ", "last_name": "ValidLast"},
            {"first_name": "ValidFirst", "last_name": ""},
            {"first_name": "ValidFirst", "last_name": "  "},
        ]

        for invalid_name_data in invalid_name_data_list:
            invalid_user_data = self.valid_user_data.copy()
            invalid_user_data.update(invalid_name_data)
            response = self.client.post(
                self.register_url, invalid_user_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            if invalid_name_data["first_name"].strip() == "":
                self.assertIn("first_name", response.data)
            if invalid_name_data["last_name"].strip() == "":
                self.assertIn("last_name", response.data)
        self.assertEqual(CustomUser.objects.count(), 0)
