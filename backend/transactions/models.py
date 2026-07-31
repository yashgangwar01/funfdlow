from django.db import models
from django.conf import settings
from categories.models import Category


class Transaction(models.Model):
    TYPE_CHOICES = (
        ('EXPENSE', 'Expense'),
        ('ALLOCATION', 'Allocation'),
        ('AUTO_TRANSFER', 'Auto Transfer / Smart Cover'),
        ('ADJUSTMENT', 'Manual Adjustment'),
    )

    SOURCE_CHOICES = (
        ('MANUAL', 'Manual Entry'),
        ('AUTO_DETECTED', 'Auto-Detected'),
        ('USER_CORRECTED', 'User Corrected'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='EXPENSE')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='MANUAL')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.TextField(blank=True)
    merchant = models.CharField(max_length=150, blank=True)
    date = models.DateField(auto_now_add=True)
    receipt_tag = models.CharField(max_length=100, blank=True)
    is_recurring = models.BooleanField(default=False)
    bank_transaction = models.ForeignKey('BankTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.type} - {self.amount} ({self.category.name})"


class BankTransaction(models.Model):
    TYPE_CHOICES = (
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    )

    STATUS_CHOICES = (
        ('AUTO_MATCHED', 'Auto Matched'),
        ('NEEDS_REVIEW', 'Needs Review'),
        ('CONFIRMED', 'Confirmed'),
        ('IGNORED', 'Ignored'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bank_transactions')
    bank_transaction_ref = models.CharField(max_length=100, unique=True, help_text="Unique transaction reference for de-duplication")
    raw_narration = models.TextField()
    normalized_merchant = models.CharField(max_length=150, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='DEBIT')
    date = models.DateField()
    matched_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_matches')
    consent_request = models.ForeignKey('bank_sync.ConsentRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_transactions')
    confidence_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEEDS_REVIEW')
    linked_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='bank_transaction_source')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"BankTx {self.bank_transaction_ref}: {self.normalized_merchant} ({self.amount})"


class MerchantCategoryMap(models.Model):
    SOURCE_CHOICES = (
        ('SYSTEM_DEFAULT', 'System Default'),
        ('USER_CONFIRMED', 'User Confirmed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='merchant_maps')
    merchant_pattern = models.CharField(max_length=150, db_index=True, help_text="Uppercase merchant key e.g. SWIGGY")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='merchant_mappings')
    match_count = models.IntegerField(default=1)
    last_confirmed_at = models.DateTimeField(auto_now=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='USER_CONFIRMED')

    class Meta:
        unique_together = ('user', 'merchant_pattern')
        ordering = ['-last_confirmed_at']

    def __str__(self):
        return f"{self.user.email if self.user else 'GLOBAL'}: {self.merchant_pattern} -> {self.category.name}"


class OverflowRule(models.Model):
    TRANSFER_TYPES = (
        ('FIXED_AMOUNT', 'Fixed Amount'),
        ('COVER_DEFICIT', 'Cover Full Deficit'),
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='overflow_rules', help_text="Category protected by this rule")
    source_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='source_overflow_rules', help_text="Source category (e.g. Savings) supplying funds")
    trigger_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Balance threshold that triggers transfer")
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, default='COVER_DEFICIT')
    transfer_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_transfers_per_month = models.IntegerField(default=5)
    priority = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['priority', 'id']

    def __str__(self):
        return f"Smart Cover: {self.category.name} <- {self.source_category.name}"


class AutoTransferLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='auto_transfer_logs')
    rule = models.ForeignKey(OverflowRule, on_delete=models.SET_NULL, null=True, related_name='logs')
    from_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transfers_sent')
    to_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='transfers_received')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AutoTransfer {self.amount} from {self.from_category.name} to {self.to_category.name}"
