from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from stocks.models import Position
from django.core.exceptions import ValidationError

class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class CreateEquityPosition(forms.ModelForm):
    class Meta:
       model = Position
       fields = ["symbol", "amount_invested", "price"]
       error_messages={
           "amount_invested":{"min_value": "Amount invested should be greater than 1$!"}
       }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["symbol"].widget.attrs["readonly"] = True
        self.fields["price"].widget.attrs["readonly"] = True


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']