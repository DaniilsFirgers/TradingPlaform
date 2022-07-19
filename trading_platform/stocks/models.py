from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
# Create your models here.



class Position(models.Model):
    """An equity position"""

    symbol = models.CharField(max_length=20)
    amount_invested = models.FloatField(validators=[MinValueValidator(1.0, ("Amount invested should be greater than 1$!"))])
    price = models.FloatField()
    date_acquired = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.symbol

    @property
    def shares(self):
        number_of_shares = round(self.amount_invested / self.price, 2)
        return number_of_shares

    def get_absolute_url(self):
        return reverse('home')


