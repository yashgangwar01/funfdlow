from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = (
        ('BILL_DUE', 'Bill Due Reminder'),
        ('BUDGET_ALERT', 'Budget Alert'),
        ('AUTO_TRANSFER', 'Smart Cover Auto-Transfer'),
        ('AI_INSIGHT', 'AI Financial Insight'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='BUDGET_ALERT')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user.email}"
