from django.urls import path

from .views import MyWalletView

urlpatterns = [
    path('me/', MyWalletView.as_view(), name='my-wallet'),
]