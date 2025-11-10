import csv
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from app.models import Product, Department, MeatType, UnitOfMeasure

class Command(BaseCommand):
    help = "Load products from a CSV file (append or upsert by name+department)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to CSV file")
        parser.add_argument("--upsert", action="store_true", help="Update if product exists")

    def handle(self, csv_path, upsert, *args, **kwargs):
        created = updated = 0
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                required = {"name","price","stock","department"}
                missing = required - set(reader.fieldnames or [])
                if missing:
                    raise CommandError(f"CSV missing required columns: {', '.join(sorted(missing))}")

                for row in reader:
                    name = row["name"].strip()
                    dept = (row["department"] or "").strip().lower()
                    price = Decimal(row.get("price") or "0")
                    stock = int(row.get("stock") or 0)

                    # Optional fields
                    category = (row.get("category") or "").strip()
                    subcategory = (row.get("subcategory") or "").strip()
                    meat_type = (row.get("meat_type") or "").strip().lower() or None
                    unit = (row.get("unit") or "").strip().lower() or None
                    sku = (row.get("sku") or "").strip()
                    is_active = str(row.get("is_active", "true")).strip().lower() in {"1","true","yes","y"}

                    if dept not in Department.values:
                        raise CommandError(f"Invalid department '{dept}' for product '{name}'")

                    if meat_type and meat_type not in MeatType.values:
                        raise CommandError(f"Invalid meat_type '{meat_type}' for product '{name}'")

                    if unit and unit not in UnitOfMeasure.values:
                        raise CommandError(f"Invalid unit '{unit}' for product '{name}'")

                    defaults = {
                        "price": price,
                        "stock": stock,
                        "department": dept,
                        "category": category,
                        "subcategory": subcategory,
                        "meat_type": meat_type or "",
                        "unit": unit or "",
                        "sku": sku,
                        "is_active": is_active,
                    }

                    if upsert:
                        obj, was_created = Product.objects.update_or_create(
                            name=name,
                            department=dept,
                            defaults=defaults,
                        )
                        created += int(was_created)
                        updated += int(not was_created)
                    else:
                        Product.objects.create(name=name, **defaults)
                        created += 1

        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created}, Updated: {updated}"
        ))
