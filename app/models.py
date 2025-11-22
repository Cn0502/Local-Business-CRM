from django.db import models


class Department(models.TextChoices):
    BUTCHER = "butcher", "Butcher"
    BAKERY = "bakery", "Bakery"
    RESTAURANT = "restaurant", "Restaurant"
    GROCERY = "grocery", "Grocery"
    PROPANE = "propane", "Propane"

class MeatType(models.TextChoices):
    BEEF = "beef", "Beef"
    PORK = "pork", "Pork"
    CHICKEN = "chicken", "Chicken"
    TURKEY = "turkey", "Turkey"
    LAMB = "lamb", "Lamb"
    FISH = "fish", "Fish"
    SEAFOOD = "seafood", "Seafood"
    OTHER = "other", "Other"

class UnitOfMeasure(models.TextChoices):
    EACH = "ea", "Each"
    POUND = "lb", "Pound (lb)"
    KILOGRAM = "kg", "Kilogram (kg)"

class Product(models.Model):
    name = models.CharField(max_length=100)                         # Name of the product (e.g. "Chicken Breast")
    price = models.DecimalField(max_digits=8, decimal_places=2)     # e.g. 12.99
    #stock = models.PositiveIntegerField(default=0)                 # How many units are available
    stock = models.DecimalField(max_digits=10, decimal_places=2)    # Qty on hand
    department = models.CharField(
        max_length=20,
        choices=Department.choices,
        default=Department.BUTCHER,                                 # Default to Butcher ??? 
        db_index=True
    )
        # Generic Category Placeholder
    category = models.CharField(                # Main, Side, ???
        max_length=60, blank=True
    )
        # Generic Sub-Category Placeholder
    subcategory = models.CharField(             # Not sure on subcats yet , just in case
        max_length=60, blank=True
    )

    # butcher-specific meat type
    meat_type = models.CharField(               # only for butcher items
        max_length=12, choices=MeatType.choices, blank=True
    )

    # unit handling (for weight-based pricing)
    unit = models.CharField(                    # ea/lb/kg
        max_length=2, choices=UnitOfMeasure.choices, blank=True
    )

    # Extra fields , is_active will help
    sku = models.CharField(max_length=40, blank=True, unique=False)
    is_active = models.BooleanField(default=True)

    # Added for sales tax handling
    is_taxable = models.BooleanField(default=True)

    def __str__(self):
        return self.name

