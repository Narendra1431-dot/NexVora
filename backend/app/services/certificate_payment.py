"""Payment boundary. A real provider must implement server-side payment verification."""
import os
from fastapi import HTTPException

class DemoPaymentService:
    mode = 'DEMO'
    amount = 19900
    currency = 'INR'

    def create(self):
        return {'mode': self.mode, 'amount': self.amount, 'currency': self.currency, 'status': 'pending', 'notice': 'DEMO payment: no money is charged.'}

    def confirm(self, order, confirm_demo: bool):
        if not confirm_demo or order.get('mode') != 'DEMO':
            raise HTTPException(422, 'Explicit DEMO payment confirmation required. No money will be charged.')
        return 'demo_confirmed'

def payment_service():
    if os.getenv('CERTIFICATE_PAYMENT_MODE', 'demo').lower() != 'demo':
        raise HTTPException(503, 'Live payment provider is not configured. No charge or premium issuance is permitted.')
    return DemoPaymentService()
