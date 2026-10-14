"""Tests for the inventory app.

Covers the valcalc-backed model maths, form validation and page rendering.
"""

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
