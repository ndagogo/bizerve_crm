from django.urls import path
from . import views

app_name = 'partners'

urlpatterns = [
    path('', views.partner_dashboard, name='partner_dashboard'),
]