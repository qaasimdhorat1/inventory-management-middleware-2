"""
Serializers for inventory management.

Handles CRUD operations for categories and inventory items,
stock level updates with audit logging, and low-stock alerts.
"""

from rest_framework import serializers

from .models import Category, InventoryItem, StockChange


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for category CRUD operations.
    Includes item count for dashboard display.
    """

    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'description', 'item_count',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_item_count(self, obj: Category) -> int:
        """Return the number of items in this category."""
        return obj.items.count()

    def validate_name(self, value: str) -> str:
        """Ensure category name is unique per user."""
        request = self.context['request']
        queryset = Category.objects.filter(
            name__iexact=value,
            owner=request.user,
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "You already have a category with this name."
            )
        return value


class InventoryItemSerializer(serializers.ModelSerializer):
    """
    Serializer for inventory item CRUD operations.
    Includes computed fields for status and category details.
    """

    category_name = serializers.CharField(
        source='category.name',
        read_only=True,
        default=None,
    )
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = (
            'id', 'name', 'description', 'sku', 'quantity',
            'price', 'low_stock_threshold', 'category',
            'category_name', 'status', 'is_low_stock',
            'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'status', 'created_at', 'updated_at',
        )

    def get_is_low_stock(self, obj: InventoryItem) -> bool:
        """Check if item is at or below low stock threshold."""
        return obj.quantity <= obj.low_stock_threshold

    def validate_sku(self, value: str) -> str:
        """Ensure SKU is unique across all items."""
        queryset = InventoryItem.objects.filter(sku__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "An item with this SKU already exists."
            )
        return value.upper()

    def validate_category(self, value: Category) -> Category:
        """Ensure category belongs to the current user."""
        request = self.context['request']
        if value and value.owner != request.user:
            raise serializers.ValidationError(
                "You can only assign your own categories."
            )
        return value

    def validate_quantity(self, value: int) -> int:
        """Prevent negative stock values."""
        if value < 0:
            raise serializers.ValidationError(
                "Quantity cannot be negative."
            )
        return value

    def validate_price(self, value) -> float:
        """Ensure price is not negative."""
        if value < 0:
            raise serializers.ValidationError(
                "Price cannot be negative."
            )
        return value


class StockChangeSerializer(serializers.ModelSerializer):
    """
    Serializer for stock change audit log entries.
    """

    changed_by_username = serializers.CharField(
        source='changed_by.username',
        read_only=True,
        default=None,
    )
    item_name = serializers.CharField(
        source='item.name',
        read_only=True,
    )

    class Meta:
        model = StockChange
        fields = (
            'id', 'item', 'item_name', 'change_type',
            'quantity_changed', 'quantity_before',
            'quantity_after', 'reason', 'changed_by',
            'changed_by_username', 'created_at',
        )
        read_only_fields = (
            'id', 'quantity_before', 'quantity_after',
            'changed_by', 'created_at',
        )


class StockUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating stock levels with audit trail.
    Used for stock additions, removals, and adjustments.
    """

    CHANGE_TYPE_CHOICES = [
        ('addition', 'Stock Addition'),
        ('removal', 'Stock Removal'),
        ('adjustment', 'Stock Adjustment'),
    ]

    change_type = serializers.ChoiceField(choices=CHANGE_TYPE_CHOICES)
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(required=False, default='')

    def validate(self, attrs: dict) -> dict:
        """Validate stock removal doesn't exceed current stock."""
        item = self.context.get('item')
        if (
            attrs['change_type'] == 'removal'
            and attrs['quantity'] > item.quantity
        ):
            raise serializers.ValidationError(
                {
                    "quantity": (
                        f"Cannot remove {attrs['quantity']} units. "
                        f"Only {item.quantity} in stock."
                    )
                }
            )
        return attrs
