from django.urls import path

from authen.views import RegisterApiView

urlpatterns = [
    path('',RegisterApiView.as_view(),name='register'),
]