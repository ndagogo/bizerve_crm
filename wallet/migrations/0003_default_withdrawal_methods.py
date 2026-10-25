from django.db import migrations


def create_default_withdrawal_methods(apps, schema_editor):
    WithdrawalMethod = apps.get_model('wallet', 'WithdrawalMethod')
    defaults = [
        {
            'name': 'Bank Transfer',
            'withdrawal_type': 'bank',
            'fee_type': 'fixed',
            'fee_amount': 2.50,
            'minimum_amount': 10.00,
            'processing_time': '1-3 business days',
            'description': 'Direct transfer to your Nigerian bank account.',
        },
        {
            'name': 'Mobile Money',
            'withdrawal_type': 'mobile_money',
            'fee_type': 'percentage',
            'fee_percentage': 1.5,
            'minimum_amount': 5.00,
            'processing_time': 'Same day',
            'description': 'Transfer to your mobile money wallet.',
        },
        {
            'name': 'PayPal',
            'withdrawal_type': 'paypal',
            'fee_type': 'percentage',
            'fee_percentage': 2.0,
            'minimum_amount': 20.00,
            'processing_time': '1-2 business days',
            'description': 'Receive funds in your PayPal account.',
        },
    ]
    for data in defaults:
        WithdrawalMethod.objects.get_or_create(name=data['name'], defaults=data)


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0002_withdrawalmethod_withdrawalrequest'),
    ]

    operations = [
        migrations.RunPython(create_default_withdrawal_methods, migrations.RunPython.noop),
    ]
