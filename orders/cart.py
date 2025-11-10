# orders/cart.py
from decimal import Decimal
from django.conf import settings
from django.apps import apps


def get_product_model():
    
    return apps.get_model("app", "Product")

class Cart:
    """
    Session-backed cart.
    Stores: { "<product_id>": {"qty": int} }
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def add(self, product_id, quantity=1, override=False):
        pid = str(product_id)
        item = self.cart.get(pid, {"qty": 0})
        item["qty"] = int(quantity) if override else int(item["qty"]) + int(quantity)
        if item["qty"] <= 0:
            self.cart.pop(pid, None)
        else:
            self.cart[pid] = item
        self.save()

    def remove(self, product_id):
        pid = str(product_id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def __len__(self):
        # total item count
        return sum(int(item["qty"]) for item in self.cart.values())

    def __iter__(self):
        """
        Yields rows with: product, quantity, unit_price (Decimal), line_total (Decimal)
        """
        Product = get_product_model()
        product_ids = list(self.cart.keys())
        if not product_ids:
            return
        products = Product.objects.filter(id__in=product_ids)

        # build a quick id -> product map
        pmap = {str(p.id): p for p in products}
        for pid, item in self.cart.items():
            product = pmap.get(pid)
            if not product:
                # product was deleted; skip it
                continue
            qty = int(item["qty"])
            # assume product has a numeric/decimal 'price' field
            unit_price = Decimal(str(product.price)).quantize(Decimal("0.01"))
            line_total = (unit_price * qty).quantize(Decimal("0.01"))
            yield {
                "product": product,
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total,
            }

    def total(self):
        return sum((row["line_total"] for row in self), Decimal("0.00"))
