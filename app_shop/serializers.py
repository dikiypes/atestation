from typing import Dict, Any

from rest_framework import serializers

from .models import Supplier, Product


class SupplierSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Supplier.

    Поле debt (задолженность перед поставщиком) недоступно для обновления через API.
    """

    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ('created_at',)

    def validate(self, data):
        """
        Проверяет корректность вводимых данных:
        - Запрещает изменение значения долга через API.
        - Завод не может иметь родителя.
        - Звено без родителя не может иметь долга.
        """
        type_supplier = data.get('type_supplier', self.instance.type_supplier if self.instance else None)
        parent = data.get('parent', self.instance.parent if self.instance else None)
        debt = data.get('debt', self.instance.debt if self.instance else 0)

        if self.instance and 'debt' in data and debt != self.instance.debt:
            raise serializers.ValidationError('Ошибка: нельзя изменять значение долга через API')
        if type_supplier == 'factory' and parent:
            raise serializers.ValidationError('Ошибка: завод не может иметь родителя')
        if not parent and debt > 0:
            raise serializers.ValidationError('Ошибка: у звена без родителя не может быть долга')
        return data


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Product.
    """

    class Meta:
        model = Product
        fields = '__all__'
