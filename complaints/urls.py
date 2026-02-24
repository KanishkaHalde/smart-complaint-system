from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/submit-complaint/', views.submit_complaint, name='submit_complaint'),
    path('api/get-complaints/', views.get_complaints, name='get_complaints'),
    path('api/update-status/', views.update_status, name='update_status'),
    path('api/delete-complaint/', views.delete_complaint, name='delete_complaint'),
    path('api/submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('api/reopen-complaint/', views.reopen_complaint, name='reopen_complaint'),
    path('api/get-notifications/', views.get_notifications, name='get_notifications'),
    path('api/mark-notification-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/get-dashboard-stats/', views.get_dashboard_stats, name='get_dashboard_stats'),
    path('api/get-admin-data/', views.get_admin_data, name='get_admin_data'),
    path('api/check-reminders/', views.check_reminders, name='check_reminders'),
    path('api/get-user-session/', views.get_user_session, name='get_user_session'),
]