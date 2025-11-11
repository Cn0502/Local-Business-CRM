# orders/models.py
from decimal import Decimal
from http.client import ACCEPTED
from django.conf import settings
from django.db import models
from django.utils import timezone

from django.core.validators import MinValueValidator

from decimal import Decimal, InvalidOperation

class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CREATED = "created", "Created"
        PENDING = "pending", "Pending Payment"
        ACCEPTED = "accepted", "Accepted"
        DISPATCHED = "dispatched", "Dispatched"
        PREP = "preparing", "Preparing"
        READY = "ready", "Ready for Pickup"
        #PAID = "paid", "Paid"
        COMPLETE = "complete", "Complete"
        CANCELED = "canceled", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL, related_name="orders"
    )
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True) 

    def __str__(self):
        return f"Order #{self.pk} ({self.get_status_display()})"

    def recompute_totals(self):
        self.subtotal = sum((item.line_total for item in self.items.all()), Decimal("0.00"))
        self.discount_total = Decimal("0.00")
        self.tax_total = Decimal("0.00")
        self.shipping_total = Decimal("0.00")
        self.grand_total = self.subtotal - self.discount_total + self.tax_total + self.shipping_total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey("app.Product", on_delete=models.PROTECT, related_name="order_items")

    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=64, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )

    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = [("order", "product")]

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
