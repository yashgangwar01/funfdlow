from django.db import models
from django.conf import settings


class ConsentRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consent_requests')
    consent_handle = models.CharField(max_length=150, unique=True, help_text="Setu AA consent handle ID")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    fi_data_range_start = models.DateField(null=True, blank=True)
    fi_data_range_end = models.DateField(null=True, blank=True)
    redirect_url = models.TextField(blank=True, help_text="Setu consent webview/screen redirect URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Consent {self.consent_handle} ({self.user.email}) - {self.status}"
