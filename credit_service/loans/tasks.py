from celery import shared_task
from .models import User
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@shared_task
def calculate_credit_score(user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist.")
        return

    try:
        transactions_df = pd.read_csv('/mnt/data/transactions_data_backend_1.csv')
    except FileNotFoundError:
        logger.error("Transaction file not found.")
        return
    except Exception as e:
        logger.error(f"Error reading transactions file: {e}")
        return

    try:
        user_transactions = transactions_df[transactions_df['aadhar_id'] == user.aadhar_id]

        total_balance = 0
        for _, transaction in user_transactions.iterrows():
            if transaction['transaction_type'] == 'CREDIT':
                total_balance += transaction['amount']
            elif transaction['transaction_type'] == 'DEBIT':
                total_balance -= transaction['amount']
            else:
                logger.warning(f"Unknown transaction type: {transaction['transaction_type']}")

        if total_balance >= 1000000:
            credit_score = 900
        elif total_balance <= 10000:
            credit_score = 300
        else:
            credit_score = 300 + ((total_balance - 10000) // 15000) * 10

        user.credit_score = credit_score
        user.save()
        logger.info(f"Credit score {credit_score} saved for user {user_id}")

    except Exception as e:
        logger.error(f"Error calculating credit score for user {user_id}: {e}")
