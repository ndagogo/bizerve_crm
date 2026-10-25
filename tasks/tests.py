from decimal import Decimal
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from tasks.models import Task
from wallet.models import Wallet, WithdrawalMethod, WithdrawalRequest, Transaction
from wallet.services import credit_task_payment


class UserModelTests(TestCase):
    def test_user_str_includes_type(self):
        user = User.objects.create_user(username='staff1', password='pass', user_type='staff')
        self.assertIn('staff1', str(user))


class TaskWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin1', password='pass', user_type='admin')
        self.staff = User.objects.create_user(username='staff1', password='pass', user_type='staff')
        self.other = User.objects.create_user(username='other1', password='pass', user_type='staff')
        self.due = timezone.now() + timedelta(days=3)
        self.task = Task.objects.create(
            title='Passport renewal',
            task_type='passport_renewal',
            description='Renew passport',
            created_by=self.admin,
            assigned_to=self.staff,
            expected_completion=self.due,
            amount=Decimal('100.00'),
        )

    def test_staff_can_accept_task(self):
        self.assertTrue(self.task.can_accept())
        self.task.status = 'accepted'
        self.task.accepted_at = timezone.now()
        self.task.save()
        self.assertEqual(self.task.status, 'accepted')

    def test_approval_credits_wallet_once(self):
        self.task.status = 'completed'
        self.task.save()
        self.task.status = 'approved'
        self.task.approved_at = timezone.now()
        self.task.save()

        wallet = Wallet.objects.get(user=self.staff)
        self.assertEqual(wallet.balance, Decimal('100.00'))
        self.assertEqual(Transaction.objects.filter(task=self.task, transaction_type='credit').count(), 1)

        credit_task_payment(self.task)
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal('100.00'))

    def test_unauthorized_user_cannot_view_task(self):
        client = Client()
        client.login(username='other1', password='pass')
        response = client.get(reverse('tasks:task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 302)


class WalletTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='staff1', password='pass', user_type='staff')
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        self.method = WithdrawalMethod.objects.create(
            name='Test Bank',
            withdrawal_type='bank',
            fee_type='fixed',
            fee_amount=Decimal('2.00'),
            minimum_amount=Decimal('10.00'),
        )

    def test_credit_and_debit(self):
        self.wallet.credit(Decimal('50.00'), 'Test credit')
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('50.00'))
        self.wallet.debit(Decimal('20.00'), 'Test debit')
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('30.00'))

    def test_insufficient_balance_raises(self):
        with self.assertRaises(ValueError):
            self.wallet.debit(Decimal('10.00'), 'Should fail')

    def test_withdrawal_request_creation(self):
        self.wallet.credit(Decimal('100.00'), 'Funding')
        withdrawal = WithdrawalRequest.objects.create(
            user=self.user,
            withdrawal_method=self.method,
            amount=Decimal('50.00'),
            fee=Decimal('2.00'),
            net_amount=Decimal('48.00'),
            bank_name='Test Bank',
            account_number='123456',
            account_name='Staff One',
        )
        self.assertEqual(withdrawal.net_amount, Decimal('48.00'))


class AccountsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='pass', user_type='staff')
        self.client = Client()

    def test_logout_requires_post(self):
        self.client.login(username='user1', password='pass')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 405)

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
