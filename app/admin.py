from django.contrib import admin
from .models import Product, Department

admin.site.register(Product)

class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "department", "category", "subcategory", "meat_type", "unit", "is_active")
    list_filter = ("department", "meat_type", "unit", "is_active")
    search_fields = ("name", "sku", "category", "subcategory")