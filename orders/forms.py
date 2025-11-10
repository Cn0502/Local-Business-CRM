# orders/forms.py
from django import forms

class CheckoutForm(forms.Form):
    email = forms.EmailField(label="Email", required=True)
    notes = forms.CharField(label="Order notes", required=False, widget=forms.Textarea(attrs={"rows": 3}))
