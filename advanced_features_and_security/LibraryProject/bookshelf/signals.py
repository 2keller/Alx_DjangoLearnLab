from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.apps import apps

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    Article = apps.get_model("advanced_features_and_security", "Article")

    perms = Permission.objects.filter(
        content_type__app_label="advanced_features_and_security",
        content_type__model="article"
    )
    perm_dict = {p.codename: p for p in perms}

    viewers, _ = Group.objects.get_or_create(name="Viewers")
    editors, _ = Group.objects.get_or_create(name="Editors")
    admins, _ = Group.objects.get_or_create(name="Admins")

    viewers.permissions.set([p for p in [perm_dict.get("can_view")] if p is not None])
    editors.permissions.set([
        p for p in [
            perm_dict.get("can_view"),
            perm_dict.get("can_create"),
            perm_dict.get("can_edit"),
        ] if p is not None
    ])
    admins.permissions.set(list(perm_dict.values()))