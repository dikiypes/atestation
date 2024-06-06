from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SupplierViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
