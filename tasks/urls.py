from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Task list and detail
    path('', views.task_list, name='task_list'),
    path('<int:task_id>/', views.task_detail, name='task_detail'),
    
    # Task CRUD operations
    path('create/', views.create_task, name='create_task'),
    path('<int:task_id>/update/', views.update_task, name='update_task'),
    path('<int:task_id>/delete/', views.delete_task, name='delete_task'),
    
    # Task workflow actions
    path('<int:task_id>/accept/', views.accept_task, name='accept_task'),
    path('<int:task_id>/decline/', views.decline_task, name='decline_task'),  # Staff can decline / reject task
    path('<int:task_id>/start/', views.start_task, name='start_task'),
    path('<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('<int:task_id>/approve/', views.approve_task, name='approve_task'),
    path('<int:task_id>/query/', views.query_task, name='query_task'),
]