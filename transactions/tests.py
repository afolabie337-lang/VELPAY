from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status

from accounts.models import User
from transactions.models import Transaction


class TransferTests(APITestCase):
    def setUp(self):
        # Create two verified users — the signal auto-creates their wallets
        self.sender = User.objects.create_user(
            email='sender@velpay.com', phone_number='08011111111',
            first_name='Sender', last_name='User', password='password123',
            is_verified=True,
        )
        self.receiver = User.objects.create_user(
            email='receiver@velpay.com', phone_number='08022222222',
            first_name='Receiver', last_name='User', password='password123',
            is_verified=True,
        )

        self.sender.wallet.balance = Decimal('5000.00')
        self.sender.wallet.save()

        self.sender_token = Token.objects.create(user=self.sender).key

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

    def test_successful_transfer(self):
        self.authenticate(self.sender_token)
        response = self.client.post('/api/transactions/transfer/', {
            'receiver_account_number': self.receiver.wallet.account_number,
            'amount': '1000.00',
            'description': 'Test transfer',
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.sender.wallet.refresh_from_db()
        self.receiver.wallet.refresh_from_db()

        self.assertEqual(self.sender.wallet.balance, Decimal('4000.00'))
        self.assertEqual(self.receiver.wallet.balance, Decimal('1000.00'))
        self.assertEqual(Transaction.objects.count(), 1)

    def test_transfer_fails_with_insufficient_balance(self):
        self.authenticate(self.sender_token)
        response = self.client.post('/api/transactions/transfer/', {
            'receiver_account_number': self.receiver.wallet.account_number,
            'amount': '999999.00',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.sender.wallet.refresh_from_db()
        self.assertEqual(self.sender.wallet.balance, Decimal('5000.00'))  # unchanged

    def test_transfer_fails_to_own_wallet(self):
        self.authenticate(self.sender_token)
        response = self.client.post('/api/transactions/transfer/', {
            'receiver_account_number': self.sender.wallet.account_number,
            'amount': '100.00',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unverified_user_cannot_transfer(self):
        unverified = User.objects.create_user(
            email='unverified@velpay.com', phone_number='08033333333',
            first_name='Not', last_name='Verified', password='password123',
        )
        unverified.wallet.balance = Decimal('5000.00')
        unverified.wallet.save()
        token = Token.objects.create(user=unverified).key

        self.authenticate(token)
        response = self.client.post('/api/transactions/transfer/', {
            'receiver_account_number': self.receiver.wallet.account_number,
            'amount': '100.00',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_transfer_requires_authentication(self):
        response = self.client.post('/api/transactions/transfer/', {
            'receiver_account_number': self.receiver.wallet.account_number,
            'amount': '100.00',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)