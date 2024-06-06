from django.core.exceptions import ValidationError
from django.db.models import Model
from mptt.exceptions import InvalidMove
from rest_framework import status
from rest_framework import viewsets, filters
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Supplier, Product
from .serializers import SupplierSerializer, ProductSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.get_all_suppliers()
    serializer_class = SupplierSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['country']
    http_method_names = ['get', 'post', 'delete', 'patch']

    def destroy(self, request, *args, **kwargs):
        """
        Удаление объекта поставщика.
        """
        instance = self.get_object()
        can_delete, debtor = instance.can_be_deleted()

        if not can_delete:
            return self._deletion_error_response(instance, debtor)

        self._reparent_children(instance)
        self.perform_destroy(instance)
        Supplier.objects.rebuild()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _deletion_error_response(instance, debtor):
        if debtor == instance:
            return Response(
                {"error": f"Ошибка: нельзя удалить звено {instance.name} с долгом перед поставщиком"},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response({
                "error": f"Ошибка: нельзя удалить звено {instance.name}, так как у его поставщика "
                         f"{debtor.name} на следующем уровне иерархии есть долг"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @staticmethod
    def _reparent_children(instance):
        children = instance.get_children()
        for child in children:
            child.parent = instance.parent
            child.save()

    def update(self, request, *args, **kwargs):
        """
        Обновление объекта поставщика.
        """
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            return super().update(request, *args, **kwargs)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except InvalidMove:
            return Response({'error': 'Зацикленные отношения не допустимы'}, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.get_all_products()
    serializer_class = ProductSerializer
    http_method_names = ['get', 'post', 'delete', 'patch']
