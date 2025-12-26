from django.urls import path
from . import views

app_name = 'wsp'

urlpatterns = [
    path('', views.whatsapp_console, name='console'),
    path('bulk-consult/', views.bulk_consult, name='bulk_consult'),
    path('check-task/<str:task_id>/', views.check_task, name='check_task'),
]