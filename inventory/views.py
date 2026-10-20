"""Inventory views.

Access rules (roles come from the ``setup_roles`` groups):

* dashboard        -> any authenticated user
* product list     -> ``inventory.view_product``
* add / edit / delete -> add/change/delete_product permission
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

import valcalc

from .forms import ProductForm
from .models import Category, Product


@login_required
def dashboard(request):
    """Home page: stock totals and a category breakdown."""
    products = list(Product.objects.select_related("category"))

    total_units = valcalc.add(*[p.quantity for p in products])
    total_value = valcalc.round_money(valcalc.add(*[p.stock_value for p in products]))
    low_stock = [p for p in products if p.is_low_stock]
    restock_cost = valcalc.round_money(
        valcalc.add(*[p.restock_cost for p in low_stock])
    )

    breakdown = []
    for category in Category.objects.all():
        items = [p for p in products if p.category_id == category.pk]
        value = valcalc.round_money(valcalc.add(*[p.stock_value for p in items]))
        share = valcalc.percent_of(value, total_value) if total_value else 0.0
        breakdown.append(
            {
                "category": category,
                "count": len(items),
                "value": value,
                "share": round(share, 1),
            }
        )

    low_share = valcalc.percent_of(len(low_stock), len(products)) if products else 0.0

    context = {
        "product_count": len(products),
        "total_units": total_units,
        "total_value": total_value,
        "low_stock": low_stock,
        "low_share": round(low_share, 1),
        "restock_cost": restock_cost,
        "vat_total": valcalc.total_with_tax(total_value, 18),
        "breakdown": breakdown,
    }
    return render(request, "inventory/dashboard.html", context)


class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Product
    context_object_name = "products"
    template_name = "inventory/product_list.html"
    permission_required = "inventory.view_product"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("category")
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(sku__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = list(context["products"])
        context["products"] = products
        context["query"] = self.request.GET.get("q", "").strip()
        context["total_value"] = valcalc.round_money(
            valcalc.add(*[p.stock_value for p in products])
        )
        return context


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy("inventory:product_list")
    permission_required = "inventory.add_product"

    def form_valid(self, form):
        messages.success(
            self.request, f"“{form.cleaned_data['name']}” was added to the inventory."
        )
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy("inventory:product_list")
    permission_required = "inventory.change_product"

    def form_valid(self, form):
        messages.success(self.request, f"“{form.cleaned_data['name']}” was updated.")
        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = "inventory/product_confirm_delete.html"
    success_url = reverse_lazy("inventory:product_list")
    permission_required = "inventory.delete_product"

    def form_valid(self, form):
        messages.success(self.request, f"“{self.object.name}” was deleted.")
        return super().form_valid(form)
