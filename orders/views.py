# orders/views.py
# from decimal import Decimal
from django.apps import apps
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .cart import Cart
from .models import Order, OrderItem
from .forms import CheckoutForm

from decimal import Decimal, InvalidOperation

from django.conf import settings


from django.contrib.auth.decorators import login_required


# Added for store hours
def is_store_open():
    """
    Returns True if current local time is between 7:00 and 19:00 (7 PM),
    False otherwise.
    """
    now = timezone.localtime(timezone.now())
    hour = now.hour
    return 7 <= hour < 19    # open 07:00–18:59, closed 19:00–06:59  7 19


def _get_product_or_404(product_id: int):
    Product = apps.get_model("app", "Product")  # change "app" if needed
    try:
        return Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        raise Http404("Product not found")

def cart_add(request, product_id: int):
    _get_product_or_404(product_id)
    qty_str = request.GET.get("qty", "1")
    try:
        qty = Decimal(str(qty_str))
    except (InvalidOperation, TypeError):
        qty = Decimal("1")
    if qty <= 0:
        qty = Decimal("1")
    cart = Cart(request)
    cart.add(product_id, quantity=qty)
    messages.success(request, "Item added to cart.")


    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("product_list")   # use your actual products URL name


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

    # --- Compute preview totals using same logic style as Order.recompute_totals() ---
    # Cart subtotal (before tax & shipping)
    subtotal = cart.total()  # this already sums line_total in your Cart

    # Tax rate from settings (e.g. settings.TAX_DEFAULT_RATE = Decimal("0.0875"))
    rate = getattr(settings, "TAX_DEFAULT_RATE", Decimal("0"))

    tax_total = Decimal("0.00")
    for r in rows:
        p = r["product"]
        line_total = r["line_total"]
        # only tax taxable products, mirrors is_taxable logic in recompute_totals()
        if getattr(p, "is_taxable", True):
            line_tax = (line_total * rate).quantize(Decimal("0.01"))
            tax_total += line_tax

    shipping_total = Decimal("0.00")
    discount_total = Decimal("0.00")
    grand_total = subtotal - discount_total + tax_total + shipping_total

    store_open = is_store_open() 

    # ----- GET: show checkout page with totals -----
    if request.method == "GET":

        initial_email = ""
        initial_name = ""

        if request.user.is_authenticated:
            if getattr(request.user, "email", ""):
                initial_email = request.user.email.strip()
            # Try to prefill name from user
            full_name = request.user.get_full_name().strip()
            if full_name:
                initial_name = full_name




        form = CheckoutForm(initial={"email": initial_email, "name": initial_name})

        context = {
            "cart": cart,
            "rows": rows,
            "form": form,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "shipping_total": shipping_total,
            "discount_total": discount_total,
            "grand_total": grand_total,
            "store_open": store_open,
        }
        return render(request, "orders/checkout.html", context)

    # ----- POST: validate form -----
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        # re-render the page with same totals so user still sees the full amount
        context = {
            "cart": cart,
            "rows": rows,
            "form": form,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "shipping_total": shipping_total,
            "discount_total": discount_total,
            "grand_total": grand_total,
            "store_open": store_open,
        }
        return render(request, "orders/checkout.html", context)

    if not store_open:
        messages.error(
            request,
            "Online orders are accepted only between 7:00 AM and 7:00 PM. "
            "Please return during business hours."
        )
        context = {
            "cart": cart,
         "rows": rows,
         "form": form,
         "subtotal": subtotal,
         "tax_total": tax_total,
         "shipping_total": shipping_total,
         "discount_total": discount_total,
         "grand_total": grand_total,
         "store_open": store_open,
        }
        return render(request, "orders/checkout.html", context, status=403)


    # ----- POST valid: create order + items -----
    name = form.cleaned_data.get("name", "").strip()
    email = form.cleaned_data["email"].strip()
    phone = form.cleaned_data.get("phone", "").strip()
    # notes = form.cleaned_data.get("notes", "").strip()  # if you add notes later

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        email=email,
        customer_name=name,   # NEW
        phone=phone,          # NEW
        status=Order.Status.PENDING,
    )

    items = []
    for r in rows:
        p = r["product"]
        qty = r["quantity"]              # should already be a Decimal from Cart
        unit_price = r["unit_price"]     # Decimal
        is_taxable = getattr(p, "is_taxable", True)

        items.append(OrderItem(
            order=order,
            product=p,
            product_name=getattr(p, "name", str(p)),
            product_sku=getattr(p, "sku", "") or "",
            unit_price=unit_price,
            quantity=qty,
            is_taxable=is_taxable,
            line_total=(unit_price * qty).quantize(Decimal("0.01")),
        ))

    OrderItem.objects.bulk_create(items)

    # compute subtotal, tax, shipping, grand_total (uses is_taxable snapshots)
    order.recompute_totals()
    order.save(update_fields=["subtotal", "discount_total", "tax_total", "shipping_total", "grand_total"])

    cart.clear()
    messages.success(request, f"Order #{order.pk} created.")
    return render(request, "orders/checkout_success.html", {"order": order})

@login_required(login_url="login")
def department_orders(request):
    """
    Department workboard:
    - Filter by department (from Product.department)
    - Show all incomplete orders (not COMPLETE/CANCELED)
    - Allow changing status per order
    """
    Product = apps.get_model("app", "Product")  

    
    current_dept = request.GET.get("department", "").strip()

    # base queryset: orders that are not complete or canceled
    qs = Order.objects.exclude(
        status__in=[Order.Status.COMPLETE, Order.Status.CANCELED]
    )

    
    if current_dept:
        qs = qs.filter(items__product__department=current_dept).distinct()

    
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        new_status = request.POST.get("status", "").strip()

        
        redirect_url = reverse("department_orders")
        if current_dept:
            redirect_url += f"?department={current_dept}"

        if not order_id or not new_status:
            messages.error(request, "Missing order or status.")
            return redirect(redirect_url)

        
        valid_codes = {code for code, label in Order.Status.choices}
        if new_status not in valid_codes:
            messages.error(request, "Invalid status value.")
            return redirect(redirect_url)

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect(redirect_url)

        
        order.status = new_status
        if new_status == Order.Status.COMPLETE:
            order.completed_at = timezone.now()
        order.recompute_totals()
        order.save(
            update_fields=[
                "status",
                "subtotal",
                "discount_total",
                "tax_total",
                "shipping_total",
                "grand_total",
                "completed_at",
            ]
        )
        messages.success(
            request,
            f"Order #{order.id} updated to {order.get_status_display()}.",
        )
        return redirect(redirect_url)

    
    orders = (
        qs.select_related("user")
        .prefetch_related("items__product")
        .order_by("created_at")
    )

    
    departments = (
        Product.objects.values_list("department", flat=True)
        .distinct()
        .order_by("department")
    )

    context = {
        "departments": departments,
        "current_department": current_dept,
        "orders": orders,
        "status_choices": Order.Status.choices,
    }
    return render(request, "orders/department_orders.html", context)

def order_detail(request, order_id: int):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"), pk=order_id
    )
    return render(request, "orders/order_detail.html", {"order": order})