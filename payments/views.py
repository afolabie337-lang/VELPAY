import uuid

from django.db import transaction as db_transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.models import Transaction
from wallets.models import Wallet

from .models import PaymentIntent
from .serializers import InitializePaymentSerializer, VerifyPaymentSerializer
from .services import initialize_payment, verify_payment


class InitializePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitializePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']

        wallet = request.user.wallet
        reference = f"PAY-{uuid.uuid4().hex[:12]}"

        result = initialize_payment(request.user.email, amount, reference)
        print(result)

        if not result.get('status'):
            return Response({'error': 'Could not initialize payment.'}, status=status.HTTP_400_BAD_REQUEST)

        PaymentIntent.objects.create(wallet=wallet, reference=reference, amount=amount)

        return Response({
            'authorization_url': result['data']['authorization_url'],
            'reference': reference,
        })


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reference = serializer.validated_data['reference']

        try:
            intent = PaymentIntent.objects.get(reference=reference, wallet=request.user.wallet)
        except PaymentIntent.DoesNotExist:
            return Response({'error': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)

        if intent.status == PaymentIntent.Status.SUCCESS:
            return Response({'message': 'Already credited.'})

        result = verify_payment(reference)
        paystack_status = result.get('data', {}).get('status')

        if paystack_status == 'success':
            with db_transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(id=intent.wallet_id)
                wallet.balance += intent.amount
                wallet.save()

                intent.status = PaymentIntent.Status.SUCCESS
                intent.save()

                Transaction.objects.create(
                    reference=reference,
                    receiver_wallet=wallet,
                    amount=intent.amount,
                    transaction_type=Transaction.TransactionType.DEPOSIT,
                    status=Transaction.Status.SUCCESS,
                    description='Wallet funding via Paystack',
                )

            return Response({'message': 'Wallet funded successfully.', 'balance': wallet.balance})

        intent.status = PaymentIntent.Status.FAILED
        intent.save()
        return Response({'error': 'Payment was not successful.'}, status=status.HTTP_400_BAD_REQUEST)
    

import hashlib
import hmac

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(APIView):
    permission_classes = []  # Paystack isn't a logged-in user — no auth here
    authentication_classes = []

    def post(self, request):
        signature = request.headers.get('x-paystack-signature', '')
        computed = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            request.body,
            hashlib.sha512,
        ).hexdigest()

        if signature != computed:
            return HttpResponse(status=401)

        event = request.data
        if event.get('event') == 'charge.success':
            reference = event['data']['reference']
            self._credit_wallet(reference)

        return HttpResponse(status=200)

    def _credit_wallet(self, reference):
        try:
            intent = PaymentIntent.objects.get(reference=reference)
        except PaymentIntent.DoesNotExist:
            return

        if intent.status == PaymentIntent.Status.SUCCESS:
            return  # already credited — avoid double-crediting

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(id=intent.wallet_id)
            wallet.balance += intent.amount
            wallet.save()

            intent.status = PaymentIntent.Status.SUCCESS
            intent.save()

            Transaction.objects.create(
                reference=reference,
                receiver_wallet=wallet,
                amount=intent.amount,
                transaction_type=Transaction.TransactionType.DEPOSIT,
                status=Transaction.Status.SUCCESS,
                description='Wallet funding via Paystack (webhook)',
            )    

from .models import Withdrawal
from .serializers import WithdrawSerializer
from .services import create_transfer_recipient, initiate_transfer


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_verified:
            return Response(
                {'error': 'Please verify your account before withdrawing.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']
        bank_code = serializer.validated_data['bank_code']
        account_number = serializer.validated_data['account_number']

        wallet = request.user.wallet

        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(id=wallet.id)

            if wallet.balance < amount:
                return Response({'error': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

            recipient_result = create_transfer_recipient(
                name=f"{request.user.first_name} {request.user.last_name}",
                account_number=account_number,
                bank_code=bank_code,
            )

            if not recipient_result.get('status'):
                return Response({'error': 'Could not verify bank account.'}, status=status.HTTP_400_BAD_REQUEST)

            recipient_code = recipient_result['data']['recipient_code']
            account_name = recipient_result['data']['details']['account_name']
            reference = f"WTH-{uuid.uuid4().hex[:12]}"

            transfer_result = initiate_transfer(amount, recipient_code, reason='VelPay withdrawal')
            print(transfer_result)

            if not transfer_result.get('status'):
                return Response({'error': 'Transfer could not be initiated.'}, status=status.HTTP_400_BAD_REQUEST)

            # Debit immediately — Paystack transfer is now in progress.
            wallet.balance -= amount
            wallet.save()

            withdrawal = Withdrawal.objects.create(
                wallet=wallet,
                reference=reference,
                amount=amount,
                bank_code=bank_code,
                account_number=account_number,
                account_name=account_name,
                recipient_code=recipient_code,
                status=Withdrawal.Status.PENDING,
            )

            Transaction.objects.create(
                reference=reference,
                sender_wallet=wallet,
                amount=amount,
                transaction_type=Transaction.TransactionType.WITHDRAWAL,
                status=Transaction.Status.PENDING,
                description=f'Withdrawal to {account_name} ({account_number})',
            )

        return Response({
            'message': 'Withdrawal initiated.',
            'reference': reference,
            'balance': wallet.balance,
        })


class BankListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .services import get_bank_list
        result = get_bank_list()
        banks = [{'name': b['name'], 'code': b['code']} for b in result.get('data', [])]
        return Response(banks)
