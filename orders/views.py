# orders/views.py
from decimal import Decimal
from django.apps import apps
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from .cart import Cart
from .models import Order, OrderItem
from .forms import CheckoutForm

def _get_product_or_404(product_id: int):
    Product = apps.get_model("app", "Product")  # change "app" if needed
    try:
        return Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise Http404("Product not found")

def cart_add(request, product_id: int):
    _get_product_or_404(product_id)
    cart = Cart(request)
    qty = int(request.GET.get("qty", 1))
    cart.add(product_id, quantity=qty)
    messages.success(request, "Item added to cart.")
    return redirect("cart_detail")

def cart_remove(request, product_id: int):
    cart = Cart(request)
    cart.remove(product_id)
    messages.info(request, "Item removed.")
    return redirect("cart_detail")

def cart_detail(request):
    cart = Cart(request)
    return render(request, "orders/cart_detail.html", {"cart": cart})

@transaction.atomic
def checkout(request):
    cart = Cart(request)
    rows = list(cart)
    if not rows:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")

    # GET: show confirmation + form
    if request.method == "GET":
        initial_email = ""
        if request.user.is_authenticated and getattr(request.user, "email", ""):
            initial_email = request.user.email.strip()
        form = CheckoutForm(initial={"email": initial_email})
        return render(request, "orders/checkout.html", {"cart": cart, "rows": rows, "form": form})

    # POST: validate, create order + items
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return render(request, "orders/checkout.html", {"cart": cart, "rows": rows, "form": form})

    email = form.cleaned_data["email"].strip()
    # notes = form.cleaned_data.get("notes", "").strip()  # save later if you add a field

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        email=email,
        status=Order.Status.PENDING,
    )

    items = []
    for r in rows:
        p = r["product"]
        qty = r["quantity"]
        unit_price = r["unit_price"]
        items.append(OrderItem(
            order=order,
            product=p,
            product_name=getattr(p, "name", str(p)),
            product_sku=getattr(p, "sku", "") or "",
            unit_price=unit_price,
            quantity=qty,
            line_total=(unit_price * qty).quantize(Decimal("0.01")),
        ))
    OrderItem.objects.bulk_create(items)

    order.recompute_totals()
    order.save(update_fields=["subtotal", "discount_total", "tax_total", "shipping_total", "grand_total"])

    cart.clear()
    messages.success(request, f"Order #{order.pk} created.")
    return render(request, "orders/checkout_success.html", {"order": order})
