from django.urls import path

from .views import MyTransactionsView, TransferView

urlpatterns = [
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('history/', MyTransactionsView.as_view(), name='transaction-history'),
]

