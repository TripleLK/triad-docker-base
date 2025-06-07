from django.urls import path
from . import views

app_name = 'ai_processing'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('process/', views.process_url_view, name='process_url'),
    path('status/<int:request_id>/', views.processing_status_view, name='processing_status'),
    path('create-equipment/<int:request_id>/', views.create_lab_equipment_view, name='create_equipment'),
    path('preview/<int:request_id>/', views.preview_extraction_view, name='preview_extraction'),
    path('delete/<int:request_id>/', views.delete_request_view, name='delete_request'),
    path('retry/<int:request_id>/', views.retry_request_view, name='retry_request'),
    
    # Batch processing URLs
    path('batch/process/', views.batch_process_view, name='batch_process'),
    path('batch/status/<int:batch_id>/', views.batch_status_view, name='batch_status'),
    path('batch/delete/<int:batch_id>/', views.delete_batch_view, name='delete_batch'),
    path('batch/retry/<int:batch_id>/', views.retry_batch_view, name='retry_batch'),
    
    # API endpoints
    path('api/batch/process/', views.api_batch_process, name='api_batch_process'),
] 