import requests
from django.conf import settings

PAYSTACK_BASE_URL = 'https://api.paystack.co'


def initialize_payment(email, amount, reference):
    """amount is in Naira; Paystack expects kobo (amount * 100)."""
    url = f"{PAYSTACK_BASE_URL}/transaction/initialize"
    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    payload = {
        'email': email,
        'amount': int(amount * 100),
        'reference': reference,
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def verify_payment(reference):
    url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"
    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    response = requests.get(url, headers=headers)
    return response.json()


def create_transfer_recipient(name, account_number, bank_code):
    url = f"{PAYSTACK_BASE_URL}/transferrecipient"
    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    payload = {
        'type': 'nuban',
        'name': name,
        'account_number': account_number,
        'bank_code': bank_code,
        'currency': 'NGN',
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def initiate_transfer(amount, recipient_code, reason=''):
    url = f"{PAYSTACK_BASE_URL}/transfer"
    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    payload = {
        'source': 'balance',
        'amount': int(amount * 100),
        'recipient': recipient_code,
        'reason': reason,
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def get_bank_list():
    url = f"{PAYSTACK_BASE_URL}/bank"
    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    response = requests.get(url, headers=headers)
    return response.json()