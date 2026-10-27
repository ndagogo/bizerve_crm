from django.urls import path
from django.contrib.auth import views as auth_views
from . import password_reset_views, user_management, views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('users/', user_management.user_list, name='user_list'),
    path('users/new/', user_management.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', user_management.user_edit, name='user_edit'),
    path('users/<int:user_id>/password/', user_management.user_password, name='user_password'),
    path('users/<int:user_id>/toggle-active/', user_management.user_toggle_active, name='user_toggle_active'),
    path('session-timeout/', user_management.session_settings, name='session_settings'),

    # Password reset (forgot password)
    path(
        'password-reset/',
        password_reset_views.PasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        password_reset_views.PasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        password_reset_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        password_reset_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
]
