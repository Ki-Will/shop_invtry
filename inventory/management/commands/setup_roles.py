"""Create and repair the roles: groups, permissions, members.

Idempotent — safe to run whenever:

    python3 manage.py setup_roles

What it does:
* Groups get *exactly* the inventory permissions from ``GROUP_PERMISSIONS``
  (``set()`` also strips permissions that do not belong there — the existing
  groups had ``*_session`` permissions from the sessions app).
* Known staff users are plugged into their group (created if missing).
* Any user without a usable password gets the local demo password
  (existing passwords are never overwritten).
* A superuser is created only when the project has none.
"""

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

DEMO_PASSWORD = "ShopRole!2026"

# Group -> exactly which inventory permissions its members get.
GROUP_PERMISSIONS = {
    # Can manage the store (products), but only *see* categories.
    "Products manager": {
        "inventory.view_product",
        "inventory.add_product",
        "inventory.change_product",
        "inventory.delete_product",
        "inventory.view_category",
    },
    # Can manage categories, but only *see* the store (products).
    "Categories users": {
        "inventory.view_category",
        "inventory.add_category",
        "inventory.change_category",
        "inventory.delete_category",
        "inventory.view_product",
    },
}

# Existing staff users plugged into their group.
GROUP_MEMBERS = {
    "user1": "Categories users",
    "user2": "Categories users",
    "user3": "Products manager",
    "user4": "Products manager",
}

SUPERUSER = "admin"


class Command(BaseCommand):
    help = "Create groups, sync permissions and plug users into their roles."

    def handle(self, *args, **options):
        # 1) groups + permissions (set() replaces, so junk perms get stripped)
        for name, codenames in GROUP_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=name)
            perms = [
                Permission.objects.get(
                    content_type__app_label="inventory",
                    codename=codename.split(".")[-1],
                )
                for codename in sorted(codenames)
            ]
            group.permissions.set(perms)
            state = "created" if created else "synced"
            self.stdout.write(
                self.style.SUCCESS(
                    f"[{state}] group {name!r} -> {len(perms)} permissions"
                )
            )

        # 2) members (plug existing users, create them only if missing)
        for username, group_name in GROUP_MEMBERS.items():
            group = Group.objects.get(name=group_name)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"is_staff": True, "is_active": True},
            )
            user.groups.add(group)
            if not user.has_usable_password():
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=["password"])
                note = f"password set to local demo password ({DEMO_PASSWORD})"
            else:
                note = "existing password kept"
            state = "created" if created else "plugged"
            self.stdout.write(
                f"[{state}] user {username!r} -> {group_name!r} ({note})"
            )

        # 3) superuser: create one only if the project has none
        if User.objects.filter(is_superuser=True).exists():
            names = ", ".join(
                User.objects.filter(is_superuser=True).values_list(
                    "username", flat=True
                )
            )
            self.stdout.write(f"[kept] existing superuser(s): {names}")
        else:
            User.objects.create_superuser(
                SUPERUSER, email="", password=DEMO_PASSWORD
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[created] superuser {SUPERUSER!r} "
                    f"(password: {DEMO_PASSWORD})"
                )
            )

        # 4) summary
        self.stdout.write("\nRoles now:")
        for group in Group.objects.prefetch_related("user_set").order_by("name"):
            members = ", ".join(
                sorted(group.user_set.values_list("username", flat=True))
            )
            count = group.permissions.count()
            self.stdout.write(
                f"  {group.name}: {count} permissions | members: {members or '-'}"
            )
