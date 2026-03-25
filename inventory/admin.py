"""
Admin configuration for inventory models.
"""

from django.contrib import admin

from .models import Category, InventoryItem, StockChange


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at', 'updated_at')
    list_filter = ('owner',)
    search_fields = ('name', 'description')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'sku', 'quantity', 'price',
        'status', 'category', 'owner',
    )
    list_filter = ('status', 'category', 'owner')
    search_fields = ('name', 'sku', 'description')


@admin.register(StockChange)
class StockChangeAdmin(admin.ModelAdmin):
    list_display = (
        'item', 'change_type', 'quantity_changed',
        'quantity_before', 'quantity_after', 'changed_by',
        'created_at',
    )
    list_filter = ('change_type', 'changed_by')
    search_fields = ('item__name', 'reason')