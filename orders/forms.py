# orders/forms.py
from django import forms

class CheckoutForm(forms.Form):
    email = forms.EmailField(label="Email", required=False)
    notes = forms.CharField(label="Order notes", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    name = forms.CharField(label="Name",max_length=100, required=True) # True required
    phone = forms.CharField(
        label="Phone number",
        max_length=20,
        required=True,      # True required
        widget=forms.TextInput(attrs={"type": "tel"}),
    )
