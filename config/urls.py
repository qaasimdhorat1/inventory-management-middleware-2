"""
Root URL configuration for Inventory Management System.

Routes API requests to appropriate app-level URL configurations.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/inventory/', include('inventory.urls')),
]