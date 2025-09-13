from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Book

admin.site.register(Book)

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Add custom fields to the admin form
    fieldsets = list(UserAdmin.fieldsets) + [
        (None, {'fields': ('date_of_birth', 'profile_photo')}),
    ]

 
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('date_of_birth', 'profile_photo')}),
    )


    list_display = ['username', 'email', 'date_of_birth', 'is_staff', 'is_superuser']

admin.site.register(CustomUser, CustomUserAdmin)