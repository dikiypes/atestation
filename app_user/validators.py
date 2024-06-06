from django.core.exceptions import ValidationError


class CustomPasswordValidator:
    @staticmethod
    def validate(password, user=None):
        """
        Проверяет пароль на соответствие определенным критериям.
        """
        if len(password) < 8:
            raise ValidationError("Пароль должен содержать минимум 8 символов.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру.")
        if not any(char.isalpha() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну букву.")

    @staticmethod
    def get_help_text() -> str:
        """
        Возвращает текст с описанием требований к паролю.
        """
        message = """
        Пароль должен соответствовать следующим требованиям:
        - Минимум 8 символов
        - Хотя бы одна цифра
        - Хотя бы одна буква
        """
        return message
