from django.urls import path

from .views import (
    BankListView,
    InitializePaymentView,
    PaystackWebhookView,
    VerifyPaymentView,
    WithdrawView,
)

urlpatterns = [
    path('initialize/', InitializePaymentView.as_view(), name='initialize-payment'),
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
    path('withdraw/', WithdrawView.as_view(), name='withdraw'),
    path('banks/', BankListView.as_view(), name='bank-list'),
]