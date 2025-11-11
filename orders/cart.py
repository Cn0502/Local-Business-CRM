# orders/cart.py
from decimal import Decimal
from django.conf import settings
from django.apps import apps

def get_product_model():
    return apps.get_model("app", "Product") 

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def add(self, product_id, quantity="1", override=False):
        pid = str(product_id)
        # store as string
        try:
            qty_in = Decimal(str(quantity))
        except Exception:
            qty_in = Decimal("1")

        if qty_in <= 0:
            self.cart.pop(pid, None)
        else:
            item = self.cart.get(pid, {"qty": "0"})
            current = Decimal(str(item["qty"]))
            new_qty = qty_in if override else (current + qty_in)
            item["qty"] = str(new_qty.quantize(Decimal("0.01")))
            self.cart[pid] = item

        self.save()

    def remove(self, product_id):
        pid = str(product_id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def __len__(self):
        return int(sum(Decimal(str(i["qty"])) for i in self.cart.values()))

    def __iter__(self):
        Product = get_product_model()
        ids = list(self.cart.keys())
        if not ids:
            return
        products = Product.objects.filter(id__in=ids).only("id", "name", "sku", "price")
        pmap = {str(p.id): p for p in products}
        for pid, item in self.cart.items():
            product = pmap.get(pid)
            if not product:
                continue
            qty = Decimal(str(item["qty"]))                      # decimal qty
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
