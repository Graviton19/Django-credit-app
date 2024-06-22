from django_cron import CronJobBase, Schedule
from .models import Loan, Billing
from datetime import timedelta
from django.utils import timezone

class BillingCronJob(CronJobBase):
    RUN_EVERY_MINS = 1440 
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'loans.billing_cron_job'

    def do(self):
        today = timezone.now().date()
        loans = Loan.objects.filter(status='ACTIVE')
        for loan in loans:
            last_billing = Billing.objects.filter(loan=loan).order_by('-billing_date').first()
            if last_billing and (today - last_billing.billing_date).days >= 30:
                days_since_last_billing = (today - last_billing.billing_date).days
                
                daily_interest_rate = loan.interest_rate / 365 / 100
                interest_due = loan.loan_amount * daily_interest_rate * days_since_last_billing
                
                min_due = max(loan.loan_amount * 0.05, 100)
       
                Billing.objects.create(
                    loan=loan,
                    billing_date=today,
                    due_date=today + timedelta(days=30),
                    min_due=min_due,
                    principal_due=loan.loan_amount / loan.term_period,  # Assuming equal monthly payments
                    interest_due=interest_due
                )
