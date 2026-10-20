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

## Users, groups & roles

Everything (app **and** `/admin/`) requires login; each view additionally
requires its permission. Staff are split into two groups:

| Group | Members | Can do |
|---|---|---|
| Products manager | `user3`, `user4` | add/edit/delete **products** (app + admin); view categories |
| Categories users | `user1`, `user2` | manage **categories** in the admin; view products read-only |

- Superuser: `admin` (create your own with `python3 manage.py createsuperuser`).
- `python3 manage.py setup_roles` — **idempotent**; creates/repairs the groups,
  plugs the users in, gives password-less users the local demo password
  `ShopRole!2026`, and creates a superuser only if none exists.
- Unauthenticated visitors are sent to `/accounts/login/`; a 403 page names
  the role that is missing the permission. Nav links are hidden per permission.

## Run it

```bash
python3 manage.py migrate
python3 manage.py setup_roles       # groups, users, demo passwords
python3 manage.py test              # 13 tests
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
    ├── management/commands/setup_roles.py   # roles bootstrap
    └── templates/inventory/*.html
```

Plus `templates/registration/login.html` and `templates/403.html`.
