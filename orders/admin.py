from decimal import Decimal
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product", "quantity", "product_name", "product_sku", "unit_price", "line_total", "tax_rate", "tax_amount",)
    readonly_fields = ("product_name", "product_sku", "unit_price", "line_total","tax_rate","tax_amount",)

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

    actions = [
        "mark_accepted",
        "mark_dispatched",
        "mark_preparing",
        "mark_ready",
        "mark_complete",
        "mark_canceled",
    ]

    list_filter = ("status",)

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

    def _bulk_set_status(self, request, queryset, new_status):
        updated = queryset.update(status=new_status)
        self.message_user(request, f"{updated} order(s) marked {new_status}.")

    def mark_accepted(self, request, queryset):
        self._bulk_set_status(request, queryset, Order.Status.ACCEPTED)
    mark_accepted.short_description = "Mark as Accepted"

    def mark_dispatched(self, request, queryset):
        self._bulk_set_status(request, queryset, Order.Status.DISPATCHED)
    mark_dispatched.short_description = "Mark as Dispatched"

    def mark_preparing(self, request, queryset):
        self._bulk_set_status(request, queryset, Order.Status.PREP)
    mark_preparing.short_description = "Mark as Preparing"

    def mark_ready(self, request, queryset):
        self._bulk_set_status(request, queryset, Order.Status.READY)
    mark_ready.short_description = "Mark as Ready"

    def mark_complete(self, request, queryset):
        self._bulk_set_status(request, queryset, Order.Status.COMPLETE)
    mark_complete.short_description = "Mark as Complete"

    def mark_canceled(self, request, queryset):
        self._bulk_set_status(request, queryset, Order.Status.CANCELED)
    mark_canceled.short_description = "Mark as Canceled"

