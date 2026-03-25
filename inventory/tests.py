"""
Tests for inventory management.

Covers CRUD operations for categories and items, stock management
with audit logging, low-stock alerts, dashboard, and edge cases.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from .models import Category, InventoryItem, StockChange


class CategoryTests(TestCase):
    """Tests for category CRUD endpoints."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=self.user)
        self.categories_url = '/api/inventory/categories/'

    def test_create_category(self) -> None:
        """Test creating a new category."""
        response = self.client.post(self.categories_url, {
            'name': 'Electronics',
            'description': 'Electronic devices and components',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Electronics')
        self.assertEqual(Category.objects.count(), 1)

    def test_list_categories(self) -> None:
        """Test listing categories for authenticated user."""
        Category.objects.create(
            name='Electronics', owner=self.user
        )
        Category.objects.create(
            name='Furniture', owner=self.user
        )
        response = self.client.get(self.categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_update_category(self) -> None:
        """Test updating a category."""
        category = Category.objects.create(
            name='Electronics', owner=self.user
        )
        response = self.client.patch(
            f'{self.categories_url}{category.id}/',
            {'name': 'Updated Electronics'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Electronics')

    def test_delete_category(self) -> None:
        """Test deleting a category."""
        category = Category.objects.create(
            name='Electronics', owner=self.user
        )
        response = self.client.delete(
            f'{self.categories_url}{category.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 0)

    def test_duplicate_category_name(self) -> None:
        """Test creating a category with duplicate name fails."""
        Category.objects.create(name='Electronics', owner=self.user)
        response = self.client.post(self.categories_url, {
            'name': 'Electronics',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_category_ownership_isolation(self) -> None:
        """Test users cannot see other users' categories."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!',
        )
        Category.objects.create(name='Other Cat', owner=other_user)
        response = self.client.get(self.categories_url)
        self.assertEqual(len(response.data['results']), 0)

    def test_category_unauthenticated(self) -> None:
        """Test category access denied without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.categories_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class InventoryItemTests(TestCase):
    """Tests for inventory item CRUD endpoints."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=self.user)
        self.items_url = '/api/inventory/items/'
        self.category = Category.objects.create(
            name='Electronics', owner=self.user
        )
        self.valid_item_data = {
            'name': 'Laptop',
            'description': 'Business laptop',
            'sku': 'LAP-001',
            'quantity': 50,
            'price': '999.99',
            'low_stock_threshold': 10,
            'category': self.category.id,
        }

    def test_create_item(self) -> None:
        """Test creating a new inventory item."""
        response = self.client.post(self.items_url, self.valid_item_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Laptop')
        self.assertEqual(response.data['sku'], 'LAP-001')
        self.assertEqual(response.data['status'], 'in_stock')

    def test_list_items(self) -> None:
        """Test listing inventory items for authenticated user."""
        InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
        )
        response = self.client.get(self.items_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_update_item(self) -> None:
        """Test updating an inventory item."""
        item = InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
        )
        response = self.client.patch(
            f'{self.items_url}{item.id}/',
            {'name': 'Updated Laptop', 'price': '1099.99'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Laptop')

    def test_delete_item(self) -> None:
        """Test deleting an inventory item."""
        item = InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
        )
        response = self.client.delete(f'{self.items_url}{item.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(InventoryItem.objects.count(), 0)

    def test_duplicate_sku(self) -> None:
        """Test creating item with duplicate SKU fails."""
        InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
        )
        response = self.client.post(self.items_url, self.valid_item_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_quantity_rejected(self) -> None:
        """Test that negative quantity is rejected."""
        data = self.valid_item_data.copy()
        data['quantity'] = -5
        response = self.client.post(self.items_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_price_rejected(self) -> None:
        """Test that negative price is rejected."""
        data = self.valid_item_data.copy()
        data['price'] = '-10.00'
        response = self.client.post(self.items_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_item_ownership_isolation(self) -> None:
        """Test users cannot see other users' items."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!',
        )
        InventoryItem.objects.create(
            name='Other Item', sku='OTH-001', quantity=10,
            price=Decimal('50.00'), owner=other_user,
        )
        response = self.client.get(self.items_url)
        self.assertEqual(len(response.data['results']), 0)

    def test_filter_by_category(self) -> None:
        """Test filtering items by category."""
        InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
            category=self.category,
        )
        InventoryItem.objects.create(
            name='Desk', sku='DSK-001', quantity=20,
            price=Decimal('299.99'), owner=self.user,
        )
        response = self.client.get(
            f'{self.items_url}?category={self.category.id}'
        )
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_by_status(self) -> None:
        """Test filtering items by status."""
        InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
        )
        InventoryItem.objects.create(
            name='Mouse', sku='MOU-001', quantity=0,
            price=Decimal('29.99'), owner=self.user,
        )
        response = self.client.get(
            f'{self.items_url}?status=out_of_stock'
        )
        self.assertEqual(len(response.data['results']), 1)

    def test_search_items(self) -> None:
        """Test searching items by name and SKU."""
        InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
        )
        response = self.client.get(f'{self.items_url}?search=laptop')
        self.assertEqual(len(response.data['results']), 1)


class AutoStatusTests(TestCase):
    """Tests for automatic status updates based on stock levels."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )

    def test_in_stock_status(self) -> None:
        """Test item is marked in_stock when above threshold."""
        item = InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), low_stock_threshold=10,
            owner=self.user,
        )
        self.assertEqual(item.status, 'in_stock')

    def test_low_stock_status(self) -> None:
        """Test item is marked low_stock at threshold."""
        item = InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=10,
            price=Decimal('999.99'), low_stock_threshold=10,
            owner=self.user,
        )
        self.assertEqual(item.status, 'low_stock')

    def test_out_of_stock_status(self) -> None:
        """Test item is marked out_of_stock at zero."""
        item = InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=0,
            price=Decimal('999.99'), owner=self.user,
        )
        self.assertEqual(item.status, 'out_of_stock')


class StockUpdateTests(TestCase):
    """Tests for stock update endpoint with audit logging."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=self.user)
        self.item = InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
        )
        self.stock_url = f'/api/inventory/items/{self.item.id}/stock/'

    def test_stock_addition(self) -> None:
        """Test adding stock increases quantity."""
        response = self.client.post(self.stock_url, {
            'change_type': 'addition',
            'quantity': 20,
            'reason': 'New shipment arrived',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['change']['quantity_after'], 70)

    def test_stock_removal(self) -> None:
        """Test removing stock decreases quantity."""
        response = self.client.post(self.stock_url, {
            'change_type': 'removal',
            'quantity': 10,
            'reason': 'Sold to customer',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['change']['quantity_after'], 40)

    def test_stock_removal_exceeds_quantity(self) -> None:
        """Test removing more than available stock fails."""
        response = self.client.post(self.stock_url, {
            'change_type': 'removal',
            'quantity': 100,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stock_adjustment(self) -> None:
        """Test stock adjustment sets exact quantity."""
        response = self.client.post(self.stock_url, {
            'change_type': 'adjustment',
            'quantity': 25,
            'reason': 'Physical count correction',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['change']['quantity_after'], 25)

    def test_audit_log_created(self) -> None:
        """Test stock change creates audit log entry."""
        self.client.post(self.stock_url, {
            'change_type': 'addition',
            'quantity': 10,
            'reason': 'Restock',
        })
        self.assertEqual(StockChange.objects.count(), 1)
        change = StockChange.objects.first()
        self.assertEqual(change.quantity_before, 50)
        self.assertEqual(change.quantity_after, 60)
        self.assertEqual(change.changed_by, self.user)

    def test_stock_update_other_users_item(self) -> None:
        """Test cannot update stock on another user's item."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!',
        )
        other_item = InventoryItem.objects.create(
            name='Other Item', sku='OTH-001', quantity=10,
            price=Decimal('50.00'), owner=other_user,
        )
        response = self.client.post(
            f'/api/inventory/items/{other_item.id}/stock/',
            {'change_type': 'addition', 'quantity': 5},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StockHistoryTests(TestCase):
    """Tests for stock change history endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=self.user)
        self.item = InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), owner=self.user,
        )

    def test_view_stock_history(self) -> None:
        """Test viewing stock change history for an item."""
        StockChange.objects.create(
            item=self.item, change_type='addition',
            quantity_changed=10, quantity_before=50,
            quantity_after=60, changed_by=self.user,
        )
        response = self.client.get(
            f'/api/inventory/items/{self.item.id}/history/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class LowStockAlertTests(TestCase):
    """Tests for low stock alert endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=self.user)
        self.alerts_url = '/api/inventory/alerts/low-stock/'

    def test_low_stock_alerts(self) -> None:
        """Test low stock alert returns items below threshold."""
        InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=50,
            price=Decimal('999.99'), low_stock_threshold=10,
            owner=self.user,
        )
        InventoryItem.objects.create(
            name='Mouse', sku='MOU-001', quantity=3,
            price=Decimal('29.99'), low_stock_threshold=10,
            owner=self.user,
        )
        response = self.client.get(self.alerts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_out_of_stock_in_alerts(self) -> None:
        """Test out of stock items appear in alerts."""
        InventoryItem.objects.create(
            name='Keyboard', sku='KEY-001', quantity=0,
            price=Decimal('79.99'), owner=self.user,
        )
        response = self.client.get(self.alerts_url)
        self.assertEqual(len(response.data['results']), 1)


class DashboardTests(TestCase):
    """Tests for dashboard statistics endpoint."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!',
        )
        self.client.force_authenticate(user=self.user)
        self.dashboard_url = '/api/inventory/dashboard/'

    def test_dashboard_statistics(self) -> None:
        """Test dashboard returns correct summary statistics."""
        category = Category.objects.create(
            name='Electronics', owner=self.user
        )
        InventoryItem.objects.create(
            name='Laptop', sku='LAP-001', quantity=10,
            price=Decimal('1000.00'), category=category,
            owner=self.user,
        )
        InventoryItem.objects.create(
            name='Mouse', sku='MOU-001', quantity=0,
            price=Decimal('25.00'), owner=self.user,
        )
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 2)
        self.assertEqual(response.data['total_quantity'], 10)
        self.assertEqual(response.data['total_value'], 10000.00)
        self.assertEqual(response.data['out_of_stock_count'], 1)
        self.assertEqual(response.data['categories_count'], 1)

    def test_dashboard_empty(self) -> None:
        """Test dashboard with no items returns zeros."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(response.data['total_value'], 0.0)

    def test_dashboard_unauthenticated(self) -> None:
        """Test dashboard access denied without authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
