from decimal import Decimal
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "quantity", "product_name", "product_sku", "unit_price", "line_total")
    readonly_fields = ("product_name", "product_sku", "unit_price", "line_total")

    def save_new_objects(self, request, form, formset, change):
        # helper for clarity; called from save_formset
        instances = formset.save(commit=False)
        for obj in instances:
            p = obj.product
            # snapshot from product
            obj.product_name = getattr(p, "name", str(p))
            obj.product_sku = getattr(p, "sku", "") or ""
            obj.unit_price = Decimal(str(getattr(p, "price", "0.00")))
            obj.line_total = (obj.unit_price * obj.quantity).quantize(Decimal("0.01"))
            obj.save()
        formset.save_m2m()

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "email", "subtotal", "grand_total", "created_at")
    inlines = [OrderItemInline]

    def save_formset(self, request, form, formset, change):
        # populate snapshots on OrderItem before final save
        instances = formset.save(commit=False)
        for obj in instances:
            p = obj.product
            obj.product_name = getattr(p, "name", str(p))
            obj.product_sku = getattr(p, "sku", "") or ""
            obj.unit_price = Decimal(str(getattr(p, "price", "0.00")))
            obj.line_total = (obj.unit_price * obj.quantity).quantize(Decimal("0.01"))
            obj.save()
        formset.save_m2m()

    def save_related(self, request, form, formsets, change):
        # after inlines are saved, recompute order totals
        super().save_related(request, form, formsets, change)
        order = form.instance
        order.recompute_totals()
        order.save(update_fields=["subtotal", "discount_total", "tax_total", "shipping_total", "grand_total"])
