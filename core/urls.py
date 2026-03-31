from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Members
    path('api/members/', views.api_members, name='api_members'),
    path('api/members/<int:id>/', views.api_delete_member, name='api_delete_member'),

    # Absensi & History
    path('api/absensi/', views.api_absensi, name='api_absensi'),
    path('api/absensi/bulk/', views.api_absensi_bulk, name='api_absensi_bulk'), # Endpoint Baru
    path('api/absensi/<int:id>/', views.api_delete_absensi, name='api_delete_absensi'),
    path('api/history/', views.api_training_history, name='api_training_history'),

    # Kas & Report
    path('api/kas/', views.api_kas, name='api_kas'),
    path('api/kas/total/', views.api_kas_total, name='api_kas_total'),
    path('api/kas/<int:id>/', views.api_delete_kas, name='api_delete_kas'),
    path('api/report/', views.api_member_report, name='api_member_report'),
    
    # AI
    path('api/ask-ai/', views.api_ask_ai, name='api_ask_ai'),
]