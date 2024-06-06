from typing import List, Tuple, Optional

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from app_shop.validators import validate_not_blank


class Supplier(MPTTModel):
    """
    Модель поставщика или звена в сети доставки.
    """

    TYPE_CHOICES = (
        ('factory', 'Завод'),
        ('retail', 'Розничная сеть'),
        ('entrepreneur', 'Индивидуальный предприниматель'),
    )

    type_supplier = models.CharField(max_length=12, choices=TYPE_CHOICES, verbose_name='Тип звена')

    name = models.CharField(max_length=100, verbose_name='Название', validators=[validate_not_blank])
    email = models.EmailField(max_length=254, verbose_name='Электронная почта')
    country = models.CharField(max_length=100, verbose_name='Страна', validators=[validate_not_blank])
    city = models.CharField(max_length=100, verbose_name='Город', validators=[validate_not_blank])
    street = models.CharField(max_length=100, verbose_name='Улица', validators=[validate_not_blank])
    house_number = models.CharField(max_length=10, verbose_name='Номер дома', validators=[validate_not_blank])
    debt = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Задолженность перед поставщиком',
                               validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')

    parent = TreeForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children',
                            verbose_name='Поставщик')

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Звено сети'
        verbose_name_plural = 'Звенья сети'
        db_table = 'suppliers'
        unique_together = (('country', 'city', 'name', 'email'),)

    def __str__(self):
        return f'{self.get_type_supplier_display()}: {self.name}'

    @classmethod
    def get_all_suppliers(cls) -> List['Supplier']:
        """
        Возвращает список всех звеньев.
        """
        return cls.objects.all()

    def clean(self) -> None:
        """
        Проверяет правила для поставщика:
        - Завод не может иметь родителя.
        - Звено без родителя не может иметь долга.
        """

        if self.type_supplier == 'factory' and self.parent:
            raise ValidationError('Ошибка: завод не может иметь родителя')

        if not self.parent and (self.debt or 0) > 0:
            raise ValidationError('Ошибка: у звена без родителя не может быть долга')

    def can_be_deleted(self) -> Tuple[bool, Optional['Supplier']]:
        """
        Проверяет, может ли поставщик быть удален.
        Поставщик не может быть удален, если у него или у его дочерних элементов
        на следующем уровне иерархии есть долг.
        """

        if self.debt > 0:
            return False, self

        if not self.children.exists():
            return True, None

        for child in self.children.all():
            if child.debt > 0 and child.level == self.level + 1:
                return False, child

        return True, None


class Product(models.Model):
    """
    Модель продукта.
    """

    name = models.CharField(max_length=100, verbose_name='Название', validators=[validate_not_blank])
    model = models.CharField(max_length=100, verbose_name='Модель', validators=[validate_not_blank])
    release_date = models.DateField(verbose_name='Дата выхода на рынок')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, verbose_name='Поставщик')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        db_table = 'products'
        unique_together = (('name', 'model', 'release_date', 'supplier'),)

    def __str__(self):
        return f'{self.name}'

    @classmethod
    def get_all_products(cls):
        """
        Возвращает список всех продуктов.
        """
        return cls.objects.all()
