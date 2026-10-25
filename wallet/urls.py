from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # User wallet URLs
    path('', views.wallet_detail, name='wallet_detail'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('withdraw/', views.withdrawal_request, name='withdrawal_request'),
    path('withdrawals/', views.withdrawal_history, name='withdrawal_history'),
    path('withdrawals/<int:withdrawal_id>/cancel/', views.cancel_withdrawal, name='cancel_withdrawal'),
    
    # Admin withdrawal management URLs
    path('admin/withdrawals/', views.admin_withdrawal_list, name='admin_withdrawal_list'),
    path('admin/withdrawals/<int:withdrawal_id>/', views.admin_withdrawal_detail, name='admin_withdrawal_detail'),
    path('admin/withdrawal-methods/', views.admin_withdrawal_methods, name='admin_withdrawal_methods'),
    path('admin/withdrawal-methods/<int:method_id>/edit/', views.admin_edit_withdrawal_method, name='admin_edit_withdrawal_method'),
]