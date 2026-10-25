from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from wallet.models import Wallet, WithdrawalMethod, WithdrawalRequest, Transaction


class WithdrawalRefundTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin1', password='pass', user_type='admin')
        self.staff = User.objects.create_user(username='staff1', password='pass', user_type='staff')
        self.wallet = Wallet.objects.get(user=self.staff)
        self.wallet.credit(Decimal('100.00'), 'Initial')
        self.method = WithdrawalMethod.objects.create(
            name='Bank',
            withdrawal_type='bank',
            fee_type='fixed',
            fee_amount=Decimal('0.00'),
            minimum_amount=Decimal('1.00'),
        )
        self.withdrawal = WithdrawalRequest.objects.create(
            user=self.staff,
            withdrawal_method=self.method,
            amount=Decimal('40.00'),
            fee=Decimal('0.00'),
            net_amount=Decimal('40.00'),
            status='pending',
        )
        self.wallet.debit(Decimal('40.00'), f'Withdrawal #{self.withdrawal.id}')
        self.client = Client()

    def test_admin_reject_refunds_wallet(self):
        self.client.login(username='admin1', password='pass')
        response = self.client.post(
            reverse('wallet:admin_withdrawal_detail', args=[self.withdrawal.id]),
            {'status': 'rejected', 'admin_notes': 'Invalid details'},
        )
        self.assertEqual(response.status_code, 302)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100.00'))
        self.assertTrue(
            Transaction.objects.filter(
                wallet=self.wallet,
                description__contains=f'Withdrawal rejection #{self.withdrawal.id}',
            ).exists()
        )


class ApiTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staff1', password='pass', user_type='staff')
        self.client = Client()

    def test_api_requires_auth(self):
        response = self.client.get(reverse('api:task_list'))
        self.assertEqual(response.status_code, 403)

    def test_api_returns_tasks_for_staff(self):
        self.client.login(username='staff1', password='pass')
        response = self.client.get(reverse('api:task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.json())
