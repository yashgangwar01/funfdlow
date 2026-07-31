from django.db import models
from django.conf import settings


class Category(models.Model):
    ALLOCATION_TYPES = (
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    allocation_type = models.CharField(max_length=20, choices=ALLOCATION_TYPES, default='PERCENTAGE')
    allocation_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_savings_category = models.BooleanField(default=False)
    color = models.CharField(max_length=20, default='#6366f1')
    icon = models.CharField(max_length=50, default='Wallet')
    order_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_index', 'created_at']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.user.email} - {self.name}"


class AllocationRun(models.Model):
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('PARTIAL', 'Partial'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='allocation_runs')
    salary_amount = models.DecimalField(max_digits=12, decimal_places=2)
    run_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS')
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ['-run_date']

    def __str__(self):
        return f"Allocation Run {self.id} for {self.user.email} on {self.run_date.strftime('%Y-%m-%d')}"
