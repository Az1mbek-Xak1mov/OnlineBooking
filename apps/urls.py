from django.urls import include, path

urlpatterns = [
    path('', include('service.urls')),
    path('auth/', include('users.urls')),
    path('stats/', include('stats.urls')),
]
