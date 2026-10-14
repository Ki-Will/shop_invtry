"""Admin configuration for the inventory app."""

from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "product_count")

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "quantity", "unit_price", "stock_value", "is_low_stock")
    list_filter = ("category",)
    search_fields = ("name", "sku")
    ordering = ("name",)

    @admin.display(description="Stock value")
    def stock_value(self, obj):
        return f"${obj.stock_value:,.2f}"
