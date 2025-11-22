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
        from django.conf import settings
        Subtotal = Decimal("0.00")
        Tax = Decimal("0.00")

        # Recompute line totals per-line tax
        rate = getattr(settings, "TAX_DEFAULT_RATE", Decimal("0"))
        apply_shipping = bool(getattr(settings, "TAX_APPLY_TO_SHIPPING", False))
        inclusive = bool(getattr(settings, "TAX_INCLUSIVE_PRICING", False))

        for item in self.items.all():
            # line_total derived from price * qty
            item.line_total = (item.unit_price * item.quantity).quantize(Decimal("0.01"))

            # default each item’s tax to zero; set rate if taxable
            if item.is_taxable:
                item.tax_rate = rate
                if inclusive:
                    # If prices are tax-inclusive, extract tax from line_total:
                    # tax = line_total - line_total / (1 + rate)
                    denom = (Decimal("1.00") + rate)
                    item.tax_amount = (item.line_total - (item.line_total / denom)).quantize(Decimal("0.01"))
                else:
                    item.tax_amount = (item.line_total * rate).quantize(Decimal("0.01"))
            else:
                item.tax_rate = Decimal("0.0000")
                item.tax_amount = Decimal("0.00")

            item.save(update_fields=["line_total", "tax_rate", "tax_amount"])
            Subtotal += item.line_total
            Tax += item.tax_amount

        self.subtotal = Subtotal
        
        self.tax_total = Tax
        # existing discount logic:
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

    # taxable at the time of sale
    is_taxable = models.BooleanField(default=True)

    # item-level tax details
    tax_rate   = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0.0000"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = [("order", "product")]

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
