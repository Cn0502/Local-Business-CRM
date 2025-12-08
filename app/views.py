# app/views.py

"""
Definition of views.
"""

from datetime import datetime
from django.shortcuts import render
from django.http import HttpRequest
from django.apps import apps
from django.shortcuts import render
from django.db.models import Count
from django.shortcuts import redirect

from orders.cart import Cart   # <-- use the same Cart class as cart_detail

from django.utils import timezone

# Added for store hours
def is_store_open():
    """
    Returns True if current local time is between 7:00 and 19:00 (7 PM),
    False otherwise.
    """
    now = timezone.localtime(timezone.now())
    hour = now.hour
    return 7 <= hour < 19    # open 07:00–18:59, closed 19:00–06:59




def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)

    if request.user.is_authenticated and request.user.is_staff:
        return redirect("crm_dashboard")

    return render(
        request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
        }
    )

def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        }
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        }
    )


def product_list(request):
    Product = apps.get_model("app", "Product")

    # Main product list (only active items)
    products = (
        Product.objects
        .filter(is_active=True)
        .order_by("department", "name")
    )

    # ---- Cart summary using Cart helper ----
    cart = Cart(request)
    cart_items = list(cart)

    cart_total_qty = 0
    cart_total_price = 0

    for item in cart_items:
        if isinstance(item, dict):
            product = item.get("product")
            qty = int(item.get("quantity", 0))
        else:
            product = getattr(item, "product", None)
            qty = int(getattr(item, "quantity", 0))

        cart_total_qty += qty

        if product is not None:
            cart_total_price += product.price * qty

    # Added for store hours
    store_open = is_store_open()

    context = {
        "products": products,
        "cart_items": cart_items,
        "cart_total_qty": cart_total_qty,
        "cart_total_price": cart_total_price,
        "store_open": store_open, 
    }

    return render(request, "app/product_list.html", context)    



def crm_dashboard(request):
    """Renders the CRM dashboard page."""
    Product = apps.get_model("app", "Product")
    total_products = Product.objects.count()
    departments = Product.objects.values("department").distinct().count()

    context = {
        "title": "CRM Dashboard",
        "total_products": total_products,
        "departments": departments,
        "year": datetime.now().year,
    }
    return render(request, "app/crm_dashboard.html", context)

def about_page(request):
    return render(request, 'about.html')