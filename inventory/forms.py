"""Product forms whose numeric checks come from the valcalc package."""

import valcalc
from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    """ModelForm plus valcalc-backed validation.

    The field-level checks run inside ``clean_*`` so failures surface as
    normal Django form errors next to the offending field.
    """

    class Meta:
        model = Product
        fields = ["name", "sku", "category", "quantity", "unit_price", "reorder_level"]

    def clean_sku(self):
        sku = self.cleaned_data["sku"].strip().upper()
        if not all(char.isalnum() or char == "-" for char in sku):
            raise forms.ValidationError(
                "SKU may only contain letters, digits and hyphens."
            )
        return sku

    def clean_quantity(self):
        value = self.cleaned_data["quantity"]
        try:
            valcalc.validate_non_negative(value, "quantity")
            return valcalc.validate_int(value, "quantity")
        except valcalc.ValidationError as exc:
            raise forms.ValidationError(str(exc))

    def clean_unit_price(self):
        price = self.cleaned_data["unit_price"]
        try:
            valcalc.validate_positive(price, "unit_price")
        except valcalc.ValidationError as exc:
            raise forms.ValidationError(str(exc))
        return price

    def clean_reorder_level(self):
        try:
            return valcalc.validate_non_negative(
                self.cleaned_data["reorder_level"], "reorder_level"
            )
        except valcalc.ValidationError as exc:
            raise forms.ValidationError(str(exc))
