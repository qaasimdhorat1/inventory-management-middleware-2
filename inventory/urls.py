"""
URL configuration for inventory app.

Provides endpoints for category and inventory item CRUD,
stock management, audit history, and dashboard statistics.
"""

from django.urls import path

from .views import (
    CategoryDetailView,
    CategoryListCreateView,
    DashboardView,
    InventoryItemDetailView,
    InventoryItemListCreateView,
    LowStockAlertView,
    StockChangeHistoryView,
    StockUpdateView,
)

app_name = 'inventory'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path(
        'categories/',
        CategoryListCreateView.as_view(),
        name='category-list',
    ),
    path(
        'categories/<int:pk>/',
        CategoryDetailView.as_view(),
        name='category-detail',
    ),
    path('items/', InventoryItemListCreateView.as_view(), name='item-list'),
    path(
        'items/<int:pk>/',
        InventoryItemDetailView.as_view(),
        name='item-detail',
    ),
    path(
        'items/<int:pk>/stock/',
        StockUpdateView.as_view(),
        name='stock-update',
    ),
    path(
        'items/<int:pk>/history/',
        StockChangeHistoryView.as_view(),
        name='stock-history',
    ),
    path(
        'alerts/low-stock/',
        LowStockAlertView.as_view(),
        name='low-stock-alerts',
    ),
]