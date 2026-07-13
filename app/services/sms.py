"""
SMS Service — Africa's Talking integration with graceful fallback.

If AT_API_KEY is not set in the environment:
  → All SMS calls are logged to console/stdout only.
  → The system works 100% normally — no errors thrown.

To enable real SMS:
  1. Sign up at https://africastalking.com
  2. Add to your .env:
       AT_API_KEY=your_key_here
       AT_USERNAME=your_username  (use "sandbox" for testing)
       AT_SENDER_ID=JIINUE        (optional short code / sender name)
"""

import logging
import os

logger = logging.getLogger(__name__)

# ── Config (read once at import time) ──────────────────────────────────────
_API_KEY = os.getenv("AT_API_KEY")
_USERNAME = os.getenv("AT_USERNAME", "sandbox")
_SENDER = os.getenv("AT_SENDER_ID", None)

_client = None

def _get_client():
    """Lazy-initialise Africa's Talking SDK only if API key is present."""
    global _client
    if _client is not None:
        return _client
    if not _API_KEY:
        return None
    try:
        import africastalking  # type: ignore
        africastalking.initialize(_USERNAME, _API_KEY)
        _client = africastalking.SMS
        logger.info("✅ Africa's Talking SMS client initialised.")
    except ImportError:
        logger.warning(
            "africastalking package not installed. "
            "Run: pip install africastalking"
        )
    except Exception as exc:
        logger.error(f"Failed to initialise Africa's Talking: {exc}")
    return _client


def send_sms(phone: str | None, message: str) -> bool:
    """
    Send an SMS to `phone`.  Returns True if sent, False otherwise.
    Silently falls back to console logging if no API key is configured.
    """
    if not phone:
        return False

    # Normalise phone number (Kenya: 07xx → +2547xx)
    phone = phone.strip()
    if phone.startswith("07") or phone.startswith("01"):
        phone = "+254" + phone[1:]
    elif phone.startswith("7") and len(phone) == 9:
        phone = "+254" + phone

    sms = _get_client()
    if sms is None:
        # Fallback: log to console
        logger.info(f"[SMS → {phone}]: {message}")
        return True  # treat as success so callers don't error

    try:
        response = sms.send(message, [phone], sender_id=_SENDER)
        logger.info(f"SMS sent to {phone}: {response}")
        return True
    except Exception as exc:
        logger.error(f"SMS to {phone} failed: {exc}")
        return False


# ── Pre-built message templates ────────────────────────────────────────────

def sms_loan_applied(phone: str | None, member_name: str, loan_number: str, amount: str):
    send_sms(phone, f"Dear {member_name}, your loan application {loan_number} for KES {amount} has been received. Ref: JIINUE")

def sms_loan_approved(phone: str | None, member_name: str, loan_number: str):
    send_sms(phone, f"Dear {member_name}, loan {loan_number} has been APPROVED. Await disbursement. Ref: JIINUE")

def sms_loan_rejected(phone: str | None, member_name: str, loan_number: str, reason: str):
    send_sms(phone, f"Dear {member_name}, loan {loan_number} was REJECTED. Reason: {reason}. Contact office. Ref: JIINUE")

def sms_loan_disbursed(phone: str | None, member_name: str, loan_number: str, amount: str):
    send_sms(phone, f"Dear {member_name}, KES {amount} disbursed for loan {loan_number}. Repay on time. Ref: JIINUE")

def sms_payment_reminder(phone: str | None, member_name: str, loan_number: str, amount: str, due_date: str):
    send_sms(phone, f"Dear {member_name}, loan {loan_number} payment of KES {amount} is due on {due_date}. Pay on time. Ref: JIINUE")

def sms_payment_received(phone: str | None, member_name: str, loan_number: str, amount: str, balance: str):
    send_sms(phone, f"Dear {member_name}, payment of KES {amount} received for loan {loan_number}. Balance: KES {balance}. Ref: JIINUE")

def sms_missed_payment(phone: str | None, member_name: str, loan_number: str, overdue_days: int):
    send_sms(phone, f"Dear {member_name}, loan {loan_number} is {overdue_days} days overdue. Pay immediately to avoid penalties. Ref: JIINUE")

def sms_loan_closed(phone: str | None, member_name: str, loan_number: str):
    send_sms(phone, f"Dear {member_name}, congratulations! Loan {loan_number} is fully repaid. Thank you. Ref: JIINUE")

def sms_loan_rescheduled(phone: str | None, member_name: str, loan_number: str, new_installment: str):
    send_sms(phone, f"Dear {member_name}, loan {loan_number} rescheduled. New installment: KES {new_installment}. Ref: JIINUE")
