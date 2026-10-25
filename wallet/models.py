from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class Wallet(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Wallet - ${self.balance}"
    
    def credit(self, amount, description, task=None):
        """Credit money to wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        self.balance += amount
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='credit',
            description=description,
            task=task
        )
        return self.balance
    
    def debit(self, amount, description, task=None):
        """Debit money from wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient balance")
        
        self.balance -= amount
        self.save()
        
        # Create transaction record
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='debit',
            description=description,
            task=task
        )
        return self.balance

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    task = models.ForeignKey('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} - ${self.amount} - {self.wallet.user.username}"



class WithdrawalMethod(models.Model):
    WITHDRAWAL_TYPES = (
        ('bank', 'Bank Transfer'),
        ('card', 'Debit/Credit Card'),
        ('paypal', 'PayPal'),
        ('crypto', 'Cryptocurrency'),
        ('mobile_money', 'Mobile Money'),
    )
    
    FEE_TYPES = (
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    )
    
    name = models.CharField(max_length=100)
    withdrawal_type = models.CharField(max_length=20, choices=WITHDRAWAL_TYPES)
    is_active = models.BooleanField(default=True)
    fee_type = models.CharField(max_length=10, choices=FEE_TYPES, default='fixed')
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage fee (e.g., 2.5 for 2.5%)")
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    maximum_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    processing_time = models.CharField(max_length=100, default="1-3 business days")
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_withdrawal_type_display()})"
    
    def calculate_fee(self, amount):
        """Calculate withdrawal fee based on settings"""
        if self.fee_type == 'fixed':
            return self.fee_amount
        else:  # percentage
            return round((amount * self.fee_percentage) / 100, 2)
    
    def get_net_amount(self, amount):
        """Calculate net amount after fees"""
        fee = self.calculate_fee(amount)
        return amount - fee

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', '🟡 Pending'),
        ('processing', '🔵 Processing'),
        ('completed', '🟢 Completed'),
        ('rejected', '🔴 Rejected'),
        ('cancelled', '⚫ Cancelled'),
    )
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='withdrawals')
    withdrawal_method = models.ForeignKey(WithdrawalMethod, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Withdrawal details (varies by method)
    bank_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=200, blank=True)
    card_last_four = models.CharField(max_length=4, blank=True)
    paypal_email = models.EmailField(blank=True)
    crypto_wallet = models.CharField(max_length=255, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Withdrawal #{self.id} - {self.user.username} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate fee and net amount if not set
        if not self.fee and self.withdrawal_method:
            self.fee = self.withdrawal_method.calculate_fee(self.amount)
        if not self.net_amount:
            self.net_amount = self.amount - self.fee
        super().save(*args, **kwargs)
    
    def get_status_color(self):
        status_colors = {
            'pending': 'warning',
            'processing': 'info',
            'completed': 'success',
            'rejected': 'danger',
            'cancelled': 'dark',
        }
        return status_colors.get(self.status, 'secondary')
    
    def can_cancel(self):
        return self.status in ['pending', 'processing']