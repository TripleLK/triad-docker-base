from django.urls import path
from . import views
from . import api

urlpatterns = [
    # Cart URLs
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/remove-item/', views.cart_remove_item, name='cart_remove_item'),
    path('cart/items/', views.get_cart_items, name='get_cart_items'),
    path('cart/', views.cart_view, name='cart_view'),
    
    # Quote request URLs
    path('quote/request/', views.quote_request_form, name='quote_request_form'),
    path('quote/success/', views.quote_request_success, name='quote_request_success'),
    path('quote/request/<int:equipment_page_id>/', views.request_single_quote, name='request_single_quote'),
    path('quote/request/<int:equipment_page_id>/<int:equipment_model_id>/', views.request_single_quote, name='request_single_quote_with_model'),
    
    # Admin/Review URLs
    path('admin/review/', views.human_review_queue, name='human_review_queue'),
    
    # API URLs
    path('api/lab-equipment/', api.create_or_update_lab_equipment, name='api_lab_equipment'),
    path('api/approve-review-item/', api.approve_review_item, name='approve_review_item'),
] 