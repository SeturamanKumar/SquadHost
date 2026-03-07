from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_and_start_server, name='create-server'),
    path('restart/', views.restart_server, name='restart-server'),
    path('list/', views.list_servers, name='list-server'),
    path('delete/', views.delete_servers, name='delete-server'),
    path('webhook/status', views.webhook_update_status, name='webhook-update-status'),
]