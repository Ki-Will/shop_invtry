"""Template filters backed by the valcalc package.

Usage in templates:

    {% load inventory_extras %}
    {{ value|money }}                  -> 1,999.96
    {{ quantity|multiply:unit_price }} -> 1999.96
"""

from django import template

import valcalc

register = template.Library()


@register.filter
def money(value):
    """Format any number as a money string with thousands separators."""
    try:
        return f"{valcalc.round_money(value):,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter
def multiply(a, b):
    """Multiply two template variables through valcalc."""
    try:
        return valcalc.round_money(valcalc.multiply(a, b))
    except (ValueError, TypeError):
        return ""
