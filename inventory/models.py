"""
Models for the Inventory Management System.

Defines Category and InventoryItem models with full audit trails,
validation constraints, and enterprise-grade data modelling.
"""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    """
    Product category for organising inventory items.
    Each category belongs to the user who created it.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']
        unique_together = ['name', 'owner']

    def __str__(self) -> str:
        return self.name


class InventoryItem(models.Model):
    """
    Inventory item with stock tracking, categorisation,
    and low-stock alert threshold.
    """

    STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    sku = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique Stock Keeping Unit identifier',
    )
    quantity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text='Alert when stock falls below this level',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inventory_items',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_stock',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs) -> None:
        """Auto-update status based on quantity and threshold."""
        if self.quantity == 0:
            self.status = 'out_of_stock'
        elif self.quantity <= self.low_stock_threshold:
            self.status = 'low_stock'
        else:
            self.status = 'in_stock'
        super().save(*args, **kwargs)


class StockChange(models.Model):
    """
    Audit log for tracking all stock level changes.
    Provides a full history trail for enterprise compliance.
    """

    CHANGE_TYPE_CHOICES = [
        ('addition', 'Stock Addition'),
        ('removal', 'Stock Removal'),
        ('adjustment', 'Stock Adjustment'),
    ]

    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name='stock_changes',
    )
    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
    )
    quantity_changed = models.IntegerField()
    quantity_before = models.PositiveIntegerField()
    quantity_after = models.PositiveIntegerField()
    reason = models.TextField(blank=True, default='')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_changes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return (
            f"{self.change_type}: {self.quantity_changed} units "
            f"for {self.item.name}"
        )