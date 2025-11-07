from django.db import models


# p

class Product(models.Model):
    name = models.CharField(max_length=100)             # Name of the product (e.g. "Chicken Breast")
    price = models.DecimalField(max_digits=8, decimal_places=2)  # e.g. 12.99
    stock = models.PositiveIntegerField(default=0)      # How many units are available

    def __str__(self):
        return self.name
