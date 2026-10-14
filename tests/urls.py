"""Las URLs con las que se prueban las pantallas del admin."""

from django.contrib import admin
from django.urls import path

urlpatterns = [path("admin/", admin.site.urls)]
