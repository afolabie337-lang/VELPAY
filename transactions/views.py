import uuid

from django.db import transaction as db_transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from wallets.models import Wallet

from .models import Transaction
from .serializers import TransferSerializer, TransactionSerializer

from rest_framework.generics import ListAPIView
from django.db.models import Q


class TransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_verified:
            return Response(
                {'error': 'Please verify your account before making transfers.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        receiver_account_number = serializer.validated_data['receiver_account_number']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description', '')

        sender_wallet = request.user.wallet

        if sender_wallet.account_number == receiver_account_number:
            return Response({'error': 'You cannot transfer to your own wallet.'}, status=status.HTTP_400_BAD_REQUEST)
        

        try:
            receiver_wallet = Wallet.objects.get(account_number=receiver_account_number, is_active=True)
        except Wallet.DoesNotExist:
            return Response({'error': 'Receiver wallet not found.'}, status=status.HTTP_404_NOT_FOUND)

        with db_transaction.atomic():
            # lock both rows so no other request can touch these balances mid-transfer
            sender_wallet = Wallet.objects.select_for_update().get(id=sender_wallet.id)
            receiver_wallet = Wallet.objects.select_for_update().get(id=receiver_wallet.id)

            if sender_wallet.balance < amount:
                return Response({'error': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)

            sender_wallet.balance -= amount
            receiver_wallet.balance += amount
            sender_wallet.save()
            receiver_wallet.save()

            txn = Transaction.objects.create(
                reference=f"TRX-{uuid.uuid4().hex[:12]}",
                sender_wallet=sender_wallet,
                receiver_wallet=receiver_wallet,
                amount=amount,
                transaction_type=Transaction.TransactionType.TRANSFER,
                status=Transaction.Status.SUCCESS,
                description=description,
            )

        return Response(TransactionSerializer(txn).data, status=status.HTTP_201_CREATED)


class MyTransactionsView(ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        wallet = self.request.user.wallet
        return Transaction.objects.filter(
            Q(sender_wallet=wallet) | Q(receiver_wallet=wallet)
        )    