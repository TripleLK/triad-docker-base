"""
URL configuration for Lab Equipment API v2.

Created by: Quantum Gecko (system URLs)
Enhanced by: Noble Harbor (equipment URLs)
Date: 2025-01-19
Project: Triad Docker Base
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # System views
    HealthCheckView, SystemStatsView, TokenAuthView, TestView,
    # Equipment viewsets
    LabEquipmentViewSet, EquipmentModelViewSet, EquipmentAccessoryViewSet,
    CategorizedTagViewSet, QuoteCartViewSet
)

app_name = 'lab_equipment_api'

# Create DRF router for viewsets
router = DefaultRouter()
router.register(r'equipment', LabEquipmentViewSet, basename='equipment')
router.register(r'models', EquipmentModelViewSet, basename='models')
router.register(r'accessories', EquipmentAccessoryViewSet, basename='accessories')
router.register(r'tags', CategorizedTagViewSet, basename='tags')
router.register(r'cart', QuoteCartViewSet, basename='cart')

urlpatterns = [
    # ============ SYSTEM ENDPOINTS ============
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('stats/', SystemStatsView.as_view(), name='system-stats'),
    path('auth/token/', TokenAuthView.as_view(), name='token-auth'),
    path('test/', TestView.as_view(), name='test'),
    
    # ============ EQUIPMENT ENDPOINTS ============
    # Include all router URLs
    path('', include(router.urls)),
]

# Additional URL patterns for documentation and API reference
urlpatterns += [
    # Optional: Add schema/documentation endpoints if needed
    # path('schema/', ..., name='api-schema'),
    # path('docs/', ..., name='api-docs'),
] 