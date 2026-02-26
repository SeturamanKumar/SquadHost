from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_and_start_server, name='create-server'),
    path('restart/', views.restart_server, name='restart-server'),
]