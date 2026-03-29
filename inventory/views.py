"""
Views for inventory management.

Provides CRUD operations for categories and inventory items,
stock level management with audit logging, and low-stock alerts.
All endpoints require authentication and enforce ownership.
"""

from django.db.models import QuerySet
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, InventoryItem, StockChange
from .serializers import (
    CategorySerializer,
    InventoryItemSerializer,
    StockChangeSerializer,
    StockUpdateSerializer,
)


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET /api/inventory/categories/
    POST /api/inventory/categories/
    List all categories for the authenticated user or create a new one.
    """

    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        """Return categories belonging to the authenticated user."""
        return Category.objects.filter(owner=self.request.user)

    def perform_create(self, serializer: CategorySerializer) -> None:
        """Set the owner to the authenticated user on creation."""
        serializer.save(owner=self.request.user)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/inventory/categories/<id>/
    PUT/PATCH /api/inventory/categories/<id>/
    DELETE /api/inventory/categories/<id>/
    Retrieve, update, or delete a specific category.
    """

    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        """Return categories belonging to the authenticated user."""
        return Category.objects.filter(owner=self.request.user)


class InventoryItemListCreateView(generics.ListCreateAPIView):
    """
    GET /api/inventory/items/
    POST /api/inventory/items/
    List all inventory items for the authenticated user or create a new one.
    Supports search, filtering, and ordering.
    """

    serializer_class = InventoryItemSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ['name', 'sku', 'description']
    ordering_fields = [
        'name', 'quantity', 'price',
        'created_at', 'updated_at', 'status',
    ]
    ordering = ['-updated_at']

    def get_queryset(self) -> QuerySet:
        """
        Return inventory items belonging to the authenticated user.
        Supports filtering by category and status via query params.
        """
        queryset = InventoryItem.objects.filter(
            owner=self.request.user
        ).select_related('category')

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        item_status = self.request.query_params.get('status')
        if item_status:
            queryset = queryset.filter(status=item_status)

        return queryset

    def perform_create(self, serializer: InventoryItemSerializer) -> None:
        """Set the owner to the authenticated user on creation."""
        serializer.save(owner=self.request.user)


class InventoryItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/inventory/items/<id>/
    PUT/PATCH /api/inventory/items/<id>/
    DELETE /api/inventory/items/<id>/
    Retrieve, update, or delete a specific inventory item.
    """

    serializer_class = InventoryItemSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        """Return inventory items belonging to the authenticated user."""
        return InventoryItem.objects.filter(
            owner=self.request.user
        ).select_related('category')


class StockUpdateView(APIView):
    """
    POST /api/inventory/items/<id>/stock/
    Update stock levels for a specific inventory item.
    Creates an audit trail entry for every stock change.
    Sends email notification if item reaches low stock or out of stock.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, pk: int) -> Response:
        """Process a stock level change with audit logging."""
        try:
            item = InventoryItem.objects.get(
                pk=pk, owner=request.user
            )
        except InventoryItem.DoesNotExist:
            return Response(
                {"detail": "Item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StockUpdateSerializer(
            data=request.data,
            context={'item': item},
        )
        serializer.is_valid(raise_exception=True)

        change_type = serializer.validated_data['change_type']
        quantity = serializer.validated_data['quantity']
        reason = serializer.validated_data.get('reason', '')

        quantity_before = item.quantity

        if change_type == 'addition':
            item.quantity += quantity
        elif change_type == 'removal':
            item.quantity -= quantity
        elif change_type == 'adjustment':
            item.quantity = quantity

        item.save()

        quantity_changed = item.quantity - quantity_before
        StockChange.objects.create(
            item=item,
            change_type=change_type,
            quantity_changed=quantity_changed,
            quantity_before=quantity_before,
            quantity_after=item.quantity,
            reason=reason,
            changed_by=request.user,
        )

        if item.status in ('low_stock', 'out_of_stock'):
            import threading
            from django.core.mail import send_mail
            from django.conf import settings
            status_label = 'LOW STOCK' if item.status == 'low_stock' else 'OUT OF STOCK'
            item_name = item.name
            item_sku = item.sku
            item_quantity = item.quantity
            item_threshold = item.low_stock_threshold
            user_name = request.user.first_name or request.user.username
            user_email = request.user.email

            def send_stock_alert():
                try:
                    send_mail(
                        subject=f'Stock Alert: {item_name} is {status_label}',
                        message=(
                            f'Hello {user_name},\n\n'
                            f'The item "{item_name}" (SKU: {item_sku}) is now {status_label}.\n\n'
                            f'Current quantity: {item_quantity}\n'
                            f'Low stock threshold: {item_threshold}\n\n'
                            f'Please review your inventory.\n\n'
                            f'- Inventory Management System'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_email],
                        fail_silently=True,
                    )
                except Exception:
                    pass

            threading.Thread(target=send_stock_alert, daemon=True).start()

        return Response(
            {
                "message": "Stock updated successfully.",
                "item": InventoryItemSerializer(
                    item, context={'request': request}
                ).data,
                "change": {
                    "type": change_type,
                    "quantity_before": quantity_before,
                    "quantity_after": item.quantity,
                },
            },
            status=status.HTTP_200_OK,
        )


class StockChangeHistoryView(generics.ListAPIView):
    """
    GET /api/inventory/items/<id>/history/
    View the stock change audit history for a specific item.
    """

    serializer_class = StockChangeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        """Return stock changes for the specified item owned by user."""
        return StockChange.objects.filter(
            item_id=self.kwargs['pk'],
            item__owner=self.request.user,
        ).select_related('changed_by', 'item')


class LowStockAlertView(generics.ListAPIView):
    """
    GET /api/inventory/alerts/low-stock/
    List all items that are at or below their low stock threshold.
    """

    serializer_class = InventoryItemSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self) -> QuerySet:
        """Return items at or below low stock threshold."""
        return InventoryItem.objects.filter(
            owner=self.request.user,
            status__in=['low_stock', 'out_of_stock'],
        ).select_related('category')


class DashboardView(APIView):
    """
    GET /api/inventory/dashboard/
    Returns summary statistics for the inventory dashboard.
    Uses database-level aggregation for scalability.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request) -> Response:
        """Return inventory summary statistics."""
        from django.db.models import Sum, F, Count

        items = InventoryItem.objects.filter(owner=request.user)

        stats = items.aggregate(
            total_items=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('price')),
        )

        low_stock_count = items.filter(status='low_stock').count()
        out_of_stock_count = items.filter(status='out_of_stock').count()
        categories_count = Category.objects.filter(
            owner=request.user
        ).count()

        recent_changes = StockChange.objects.filter(
            item__owner=request.user
        ).select_related('item', 'changed_by')[:5]

        return Response(
            {
                "total_items": stats['total_items'] or 0,
                "total_quantity": stats['total_quantity'] or 0,
                "total_value": float(stats['total_value'] or 0),
                "low_stock_count": low_stock_count,
                "out_of_stock_count": out_of_stock_count,
                "categories_count": categories_count,
                "recent_changes": StockChangeSerializer(
                    recent_changes, many=True
                ).data,
            },
            status=status.HTTP_200_OK,
        )
