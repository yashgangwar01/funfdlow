from django.db import models
from django.conf import settings
from categories.models import Category


class Goal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=150)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    target_date = models.DateField()
    linked_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='goals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['target_date', 'id']

    def __str__(self):
        return f"{self.name} - {self.current_amount}/{self.target_amount}"
