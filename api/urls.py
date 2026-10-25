from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('tasks/', views.task_list_api, name='task_list'),
    path('tasks/<int:task_id>/', views.task_detail_api, name='task_detail'),
]
