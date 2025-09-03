from django.urls import path

from authen.views import RegisterApiView, UserListApiView

urlpatterns = [
    path('',RegisterApiView.as_view(),name='register'),
    path('/users' ,UserListApiView.as_view(),name='users')
]