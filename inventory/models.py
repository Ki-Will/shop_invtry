"""Inventory models.

Every piece of stock arithmetic is delegated to the installed ``valcalc``
package (built and published to TestPyPI from the ``valcalc/`` directory).
"""

from django.db import models

import valcalc


class Category(models.Model):
    """A product grouping, e.g. Electronics."""

    name = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """A stock item tracked by SKU."""

    name = models.CharField(max_length=128)
    sku = models.CharField(max_length=32, unique=True, help_text="e.g. LAP-0001")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    quantity = models.IntegerField(default=0, help_text="Units currently in stock")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_level = models.PositiveIntegerField(
        default=5, help_text="Low-stock alert threshold"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def stock_value(self):
        """Value of the units on hand: valcalc.multiply + valcalc.round_money."""
        return valcalc.round_money(valcalc.multiply(self.quantity, self.unit_price))

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def restock_cost(self):
        """Cost of bringing stock back up to twice the reorder level."""
        target = self.reorder_level * 2
        missing = max(target - self.quantity, 0)
        return valcalc.round_money(valcalc.multiply(missing, self.unit_price))
