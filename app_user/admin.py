from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Административный интерфейс для управления учетными записями пользователей CustomUser.
    """

    model = CustomUser
    list_display = ["pk", "email", "first_name", "last_name", "is_active"]
    list_display_links = ["pk", "email"]
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name", "pk")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Персональная информация",
            {"fields": ("first_name", "last_name")},
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("last_login", "date_joined")

    def has_module_permission(self, request):
        """
        Определяет, имеет ли пользователь разрешение.
        """
        return request.user.is_superuser

    def get_fieldsets(self, request, obj=None):
        if not obj:
            fieldsets = (
                (None, {"fields": ("email", "password1", "password2")}),
                (
                    "Персональная информация",
                    {"fields": ("first_name", "last_name")},
                ),
            )
        else:
            fieldsets = (
                (None, {"fields": ("email",)}),
                (
                    "Персональная информация",
                    {"fields": ("first_name", "last_name")},
                ),
                (
                    "Разрешения",
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "is_superuser",
                            "groups",
                            "user_permissions",
                        )
                    },
                ),
                ("Важные даты", {"fields": ("last_login", "date_joined")}),
            )
        return fieldsets
