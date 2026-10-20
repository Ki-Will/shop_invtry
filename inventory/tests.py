"""Tests for the inventory app.

Covers the valcalc-backed model maths, form validation, page rendering and
role enforcement (groups/permissions set up by ``setup_roles``).
"""

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

import valcalc

from .models import Category, Product


class InventoryTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Laptop",
            sku="LAP-0001",
            category=self.category,
            quantity=4,
            unit_price="499.99",
            reorder_level=5,
        )
        # these views are login/permission protected now — use a superuser
        boss = User.objects.create_superuser("boss", "boss@example.com", "BossPass!123")
        self.client.force_login(boss)

    def test_stock_value_comes_from_valcalc(self):
        expected = valcalc.round_money(valcalc.multiply(4, 499.99))
        self.assertEqual(self.product.stock_value, expected)
        self.assertEqual(self.product.stock_value, 1999.96)

    def test_low_stock_flag_and_restock_cost(self):
        self.assertTrue(self.product.is_low_stock)
        # target 2x reorder_level = 10, 4 in stock -> 6 missing units @ 499.99
        self.assertEqual(self.product.restock_cost, 2999.94)

    def test_dashboard_renders_totals(self):
        response = self.client.get(reverse("inventory:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1,999.96")

    def test_product_list_shows_the_product(self):
        response = self.client.get(reverse("inventory:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "LAP-0001")

    def test_form_rejects_negative_quantity(self):
        response = self.client.post(
            reverse("inventory:product_add"),
            {
                "name": "Cable",
                "sku": "CBL-0001",
                "category": self.category.pk,
                "quantity": -3,
                "unit_price": "9.99",
                "reorder_level": 2,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("quantity", response.context["form"].errors)

    def test_form_rejects_free_product(self):
        response = self.client.post(
            reverse("inventory:product_add"),
            {
                "name": "Sticker",
                "sku": "STK-0001",
                "category": self.category.pk,
                "quantity": 10,
                "unit_price": "0",
                "reorder_level": 2,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("unit_price", response.context["form"].errors)

    def test_form_accepts_valid_product(self):
        response = self.client.post(
            reverse("inventory:product_add"),
            {
                "name": "Mouse",
                "sku": "MSE-0001",
                "category": self.category.pk,
                "quantity": 12,
                "unit_price": "19.50",
                "reorder_level": 3,
            },
        )
        self.assertRedirects(response, reverse("inventory:product_list"))
        self.assertTrue(Product.objects.filter(sku="MSE-0001").exists())


class RoleTests(TestCase):
    """The two groups must only reach the part of the app they own."""

    def setUp(self):
        self.category = Category.objects.create(name="Electronics")

        self.products_group, _ = Group.objects.get_or_create(name="Products manager")
        self.products_group.permissions.set(
            Permission.objects.filter(
                content_type__app_label="inventory",
                codename__in=[
                    "view_product",
                    "add_product",
                    "change_product",
                    "delete_product",
                    "view_category",
                ],
            )
        )
        self.categories_group, _ = Group.objects.get_or_create(name="Categories users")
        self.categories_group.permissions.set(
            Permission.objects.filter(
                content_type__app_label="inventory",
                codename__in=[
                    "view_category",
                    "add_category",
                    "change_category",
                    "delete_category",
                    "view_product",
                ],
            )
        )

        self.manager = User.objects.create_user(
            "manager", password="ManagerPass!123", is_staff=True
        )
        self.manager.groups.add(self.products_group)
        self.categorizer = User.objects.create_user(
            "categorizer", password="CategorPass!123", is_staff=True
        )
        self.categorizer.groups.add(self.categories_group)

    def test_anonymous_is_sent_to_login(self):
        for url in (
            reverse("inventory:dashboard"),
            reverse("inventory:product_list"),
            reverse("inventory:product_add"),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/?next=", response["Location"])

    def test_products_manager_can_manage_the_store(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("inventory:product_add"))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("inventory:product_add"),
            {
                "name": "Desk Lamp",
                "sku": "LMP-0001",
                "category": self.category.pk,
                "quantity": 6,
                "unit_price": "15.00",
                "reorder_level": 2,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(sku="LMP-0001").exists())

    def test_products_manager_cannot_edit_categories_in_admin(self):
        self.client.force_login(self.manager)
        # may open the product add form in admin ...
        self.assertEqual(
            self.client.get(reverse("admin:inventory_product_add")).status_code, 200
        )
        # ... but not the category add form
        response = self.client.get(reverse("admin:inventory_category_add"))
        self.assertEqual(response.status_code, 403)

    def test_categories_user_cannot_edit_the_store(self):
        self.client.force_login(self.categorizer)
        # list is readable (view_product)
        self.assertEqual(
            self.client.get(reverse("inventory:product_list")).status_code, 200
        )
        # add form and its POST are forbidden
        self.assertEqual(
            self.client.get(reverse("inventory:product_add")).status_code, 403
        )
        response = self.client.post(
            reverse("inventory:product_add"),
            {
                "name": "Sneaky",
                "sku": "SNK-0001",
                "category": self.category.pk,
                "quantity": 1,
                "unit_price": "1.00",
                "reorder_level": 1,
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Product.objects.filter(sku="SNK-0001").exists())
        # and no edit links are rendered for them
        self.assertNotContains(
            self.client.get(reverse("inventory:product_list")),
            'href="/products/add/"',
        )

    def test_categories_user_can_manage_categories_in_admin(self):
        self.client.force_login(self.categorizer)
        self.assertEqual(
            self.client.get(reverse("admin:inventory_category_add")).status_code, 200
        )
        response = self.client.get(reverse("admin:inventory_product_add"))
        self.assertEqual(response.status_code, 403)


class SetupRolesCommandTests(TestCase):
    """``manage.py setup_roles`` must be idempotent and produce clean roles."""

    def test_command_builds_groups_members_and_strips_junk(self):
        call_command("setup_roles", verbosity=0)
        call_command("setup_roles", verbosity=0)  # idempotent

        products = Group.objects.get(name="Products manager")
        categories = Group.objects.get(name="Categories users")
        self.assertEqual(Group.objects.count(), 2)

        product_perms = set(products.permissions.values_list("codename", flat=True))
        self.assertEqual(
            product_perms,
            {
                "view_product",
                "add_product",
                "change_product",
                "delete_product",
                "view_category",
            },
        )
        # the junk session permissions from before must be gone
        self.assertNotIn("delete_session", product_perms)
        self.assertNotIn("add_session", set(categories.permissions.values_list("codename", flat=True)))

        # existing users plugged in, now with a usable password
        user3 = User.objects.get(username="user3")
        self.assertIn(products, user3.groups.all())
        self.assertTrue(user3.has_usable_password())
        self.assertTrue(user3.has_perm("inventory.add_product"))
        self.assertFalse(user3.has_perm("inventory.change_category"))

        user1 = User.objects.get(username="user1")
        self.assertIn(categories, user1.groups.all())
        self.assertTrue(user1.has_perm("inventory.change_category"))
        self.assertFalse(user1.has_perm("inventory.add_product"))

        # a superuser exists (created only if missing)
        self.assertTrue(User.objects.filter(is_superuser=True).exists())
