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
    products = Product.objects.all().order_by("id")
    return render(request, "app/product_list.html", {"products": products})

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