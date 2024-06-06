from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

schema_view = get_schema_view(
    openapi.Info(
        title="API Electronics Trade Network Platform",
        default_version='v1',
        description="API для платформы торговой сети электроники"
    ),
    public=True,
    permission_classes=(AllowAny,),
    authentication_classes=(JWTAuthentication,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('app_user.urls')),
    path('api/', include('app_shop.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
