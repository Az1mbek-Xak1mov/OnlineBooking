from django.urls import include, path

urlpatterns = [
    path('', include('service.urls')),
    path('auth/', include('users.urls')),
]


print(1)
