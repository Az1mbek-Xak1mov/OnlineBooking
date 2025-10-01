from django.conf.urls.static import static
from django.urls import include, path

from root import settings

urlpatterns = [
    path('', include('service.urls')),
    path('auth/', include('users.urls')),
]
