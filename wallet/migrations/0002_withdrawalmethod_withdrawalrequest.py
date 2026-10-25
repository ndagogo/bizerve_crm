# Generated manually for WithdrawalMethod and WithdrawalRequest

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WithdrawalMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('withdrawal_type', models.CharField(choices=[('bank', 'Bank Transfer'), ('card', 'Debit/Credit Card'), ('paypal', 'PayPal'), ('crypto', 'Cryptocurrency'), ('mobile_money', 'Mobile Money')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('fee_type', models.CharField(choices=[('fixed', 'Fixed Amount'), ('percentage', 'Percentage')], default='fixed', max_length=10)),
                ('fee_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('fee_percentage', models.DecimalField(decimal_places=2, default=0, help_text='Percentage fee (e.g., 2.5 for 2.5%)', max_digits=5)),
                ('minimum_amount', models.DecimalField(decimal_places=2, default=10.0, max_digits=10)),
                ('maximum_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('processing_time', models.CharField(default='1-3 business days', max_length=100)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='WithdrawalRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fee', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('net_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('bank_name', models.CharField(blank=True, max_length=200)),
                ('account_number', models.CharField(blank=True, max_length=100)),
                ('account_name', models.CharField(blank=True, max_length=200)),
                ('card_last_four', models.CharField(blank=True, max_length=4)),
                ('paypal_email', models.EmailField(blank=True, max_length=254)),
                ('crypto_wallet', models.CharField(blank=True, max_length=255)),
                ('mobile_number', models.CharField(blank=True, max_length=20)),
                ('status', models.CharField(choices=[('pending', '🟡 Pending'), ('processing', '🔵 Processing'), ('completed', '🟢 Completed'), ('rejected', '🔴 Rejected'), ('cancelled', '⚫ Cancelled')], default='pending', max_length=20)),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='withdrawals', to=settings.AUTH_USER_MODEL)),
                ('withdrawal_method', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wallet.withdrawalmethod')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
