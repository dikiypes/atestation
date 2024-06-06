from typing import Union

from django.contrib import admin, messages
from django.db.models import Prefetch
from django.db.models import QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from mptt.exceptions import InvalidMove

from .models import Product, Supplier

ERROR_DEBT_MSG = "Ошибка: нельзя удалить звено {name} с долгом перед поставщиком"
ERROR_DEBT_NEXT_LEVEL_MSG = ("Ошибка: нельзя удалить звено {name}, так как у его поставщика {debtor_name} "
                             "на следующем уровне иерархии есть долг")


class BaseAdmin(admin.ModelAdmin):
    """
    Базовый класс администратора для моделей.
    Разрешает доступ только для суперпользователей и персонала сайта.
    """

    def has_module_permission(self, request):
        """
        Проверка прав на доступ к модулю.
        """
        if request.user.is_authenticated:
            return request.user.is_superuser or request.user.is_staff
        return False

    def has_view_permission(self, request, obj):
        """
        Проверка прав на просмотр объектов.
        """
        if request.user.is_authenticated:
            return request.user.is_superuser or request.user.is_staff
        return False

    def has_change_permission(self, request, obj):
        """
        Проверка прав на изменение объектов.
        """
        if request.user.is_authenticated:
            return request.user.is_superuser or request.user.is_staff
        return False

    def has_delete_permission(self, request, obj):
        """
        Проверка прав на удаление объектов.
        """
        if request.user.is_authenticated:
            return request.user.is_superuser or request.user.is_staff
        return False

    def has_add_permission(self, request):
        """
        Проверка прав на добавление объектов.
        """
        if request.user.is_authenticated:
            return request.user.is_superuser or request.user.is_staff
        return False


@admin.register(Supplier)
class SupplierAdmin(BaseAdmin):
    """
    Административный интерфейс для управления поставщиками.

    Основные методы:
    - delete_model и delete_queryset: удаляют поставщика или группу поставщиков,
      учитывая наличие задолженности и переназначая.
    - save_model: сохраняет модель поставщика.
    - response_change, response_delete, response_action: обрабатывают ответы после выполнения
      различных действий с объектами.
    - link_to_parent: возвращает ссылку на родительский объект поставщика.
    - number_of_intermediaries: определяет количество посредников для данного поставщика.
    - clear_debt: обнуляет задолженность для выбранного набора поставщиков.
    """

    list_display = ['id', 'type_supplier', 'name', 'link_to_parent', 'number_of_intermediaries', 'debt']
    list_display_links = ['name']
    list_filter = ['city']
    actions = ['clear_debt']

    @staticmethod
    def _reassign_children_to_parent(obj):
        """
        Переназначает детей поставщика на его родительское звено.

        """
        for child in obj.get_children():
            child.parent = obj.parent
            child.save()

    @staticmethod
    def _show_debt_error_message(request, obj, debtor):
        """
        Показывает сообщение об ошибке при попытке удалить поставщика с задолженностью.
        """
        if debtor == obj:
            messages.error(request, ERROR_DEBT_MSG.format(name=obj.name))
        else:
            messages.error(request, ERROR_DEBT_NEXT_LEVEL_MSG.format(name=obj.name, debtor_name=debtor.name))

    def _handle_deletion(self, request, obj):
        """
        Обрабатывает удаление поставщика, учитывая наличие задолженности.
        """
        can_delete, debtor = obj.can_be_deleted()
        if not can_delete:
            self._show_debt_error_message(request, obj, debtor)
            return False

        self._reassign_children_to_parent(obj)
        return True

    def delete_model(self, request, obj):
        """
        Удаляет модель поставщика, учитывая наличие задолженности.
        """
        if self._handle_deletion(request, obj):
            super().delete_model(request, obj)
            Supplier.objects.rebuild()

    def delete_queryset(self, request, queryset):
        """
        Удаляет набор объектов, учитывая наличие задолженности.
        """
        queryset = queryset.prefetch_related(
            Prefetch('children', to_attr='cached_children')
        )
        ids_to_delete = []
        for obj in queryset:
            if self._handle_deletion(request, obj):
                ids_to_delete.append(obj.id)

        if ids_to_delete:
            queryset_to_delete = queryset.filter(id__in=ids_to_delete)
            super().delete_queryset(request, queryset_to_delete)
            Supplier.objects.rebuild()

    def save_model(self, request, obj, form, change):
        """
        Сохраняет модель поставщика с проверкой на циклическую зависимость.
        """
        try:
            super().save_model(request, obj, form, change)
        except InvalidMove:
            messages.error(request, "Ошибка: нельзя создать циклическую зависимость между поставщиками")

    def response_change(self, request: HttpRequest, obj: Supplier) -> HttpResponse:
        """
        Обрабатывает ответ после попытки изменения объекта.

        :param request: Запрос Django.
        :param obj: Объект поставщика, который был изменен.
        :return: HttpResponse с результатом обработки.
        """
        if messages.get_messages(request):
            reverse_url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change', args=[obj.pk])
            return HttpResponseRedirect(reverse_url)
        return super().response_change(request, obj)

    def response_delete(self, request: HttpRequest, obj_display: str, obj_id: int) -> HttpResponse:
        """
        Обрабатывает ответ после попытки удаления объекта.

        :param request: Запрос Django.
        :param obj_display: Строковое представление объекта.
        :param obj_id: Идентификатор объекта.
        :return: HttpResponse с результатом обработки.
        """
        if messages.get_messages(request):
            reverse_url = reverse(
                f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change',
                args=[obj_id]
            )
            return HttpResponseRedirect(reverse_url)
        return super().response_delete(request, obj_display, obj_id)

    def response_action(self, request, queryset):
        """
        Обрабатывает ответ после выполнения какого-либо действия над набором объектов.
        """
        response = super().response_action(request, queryset)

        all_messages = list(messages.get_messages(request))

        if any(msg.level == messages.ERROR for msg in all_messages):
            messages.set_level(request, messages.ERROR)

        for msg in all_messages:
            messages.add_message(request, msg.level, msg.message, extra_tags=msg.extra_tags)

        return response

    def link_to_parent(self, obj):
        """
        Возвращает ссылку на родительский объект поставщика.
        """
        if obj.parent:
            link = reverse("admin:app_shop_supplier_change", args=[obj.parent.id])
            return format_html('<a href="{}">{}</a>', link, obj.parent)
        return "Первое звено в цепочке"

    def number_of_intermediaries(self, obj):
        """
        Возвращает количество посредников для данного поставщика.
        """
        level = obj.get_level()
        return 'Первое звено в цепочке' if level == 0 else level - 1

    def clear_debt(self, request, queryset):
        """
        Очищает задолженность для выбранного набора поставщиков.
        """
        queryset.update(debt=0)
        self.message_user(request, "Задолженность успешно очищена для выбранных поставщиков.")

    link_to_parent.short_description = 'Поставщик'
    number_of_intermediaries.short_description = 'Количество посредников'
    clear_debt.short_description = "Очистить задолженность выбранных поставщиков"


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    """
    Административный интерфейс для управления товарами.

    - В списке отображаются следующие поля товаров: ID, имя, модель, дата выпуска и поставщик.
    - Название товара используется как ссылка, ведущая к детальной информации о товаре.
    """
    list_display = ['id', 'name', 'model', 'release_date', 'supplier']
    list_display_links = ['name']
