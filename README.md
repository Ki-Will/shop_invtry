# shop_inventory

A small **shop inventory management** project built with Django 5.2.

- `inventory` app: category + product models, CRUD views (ListView/Create/Update/Delete),
  admin registration, and a dashboard of stock totals.
- Templates in `templates/` (project-level `base.html`) and
  `inventory/templates/inventory/` rendered with Django template tags
  (`{% for %}`, `{% if %}`, `{% url %}`, `{% static %}`, custom filters…).
- Static files in `static/css/style.css` and `static/js/app.js` —
  **plain CSS and plain JS only**, no frameworks.
- All numeric validation and stock maths are delegated to the **`valcalc`**
  package built in `../valcalc/` and published to TestPyPI
  (https://test.pypi.org/project/valcalc/). It is used from:
  - `inventory/forms.py` — `validate_int`, `validate_non_negative`, `validate_positive`
  - `inventory/models.py` — `multiply`, `round_money`
  - `inventory/views.py` — `add`, `percent_of`, `total_with_tax`, `round_money`
  - `inventory/templatetags/inventory_extras.py` — `money` and `multiply` filters

## Run it

```bash
python3 manage.py migrate
python3 manage.py createsuperuser   # optional, for /admin
python3 manage.py test              # 7 tests
python3 manage.py runserver         # http://127.0.0.1:8000/
```

## Layout

```
shop_inventory/
├── manage.py
├── templates/base.html        # project-level base template
├── static/css/style.css       # plain CSS
├── static/js/app.js           # plain JS
├── shop_inventory/            # settings/urls
└── inventory/                  # the app
    ├── models.py  forms.py  views.py  urls.py  admin.py  tests.py
    ├── templatetags/inventory_extras.py
    └── templates/inventory/*.html
```
