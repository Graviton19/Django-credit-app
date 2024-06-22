from django.db import models
from django.utils import timezone
# Create your models here.
class User(models.Model):
    aadhar_id = models.CharField(max_length = 100, unique = True)
    name = models.CharField(max_length = 200)
    email = models.EmailField(unique = True)
    annual_income = models.DecimalField(max_digits = 15, decimal_places = 2)
    credit_score = models.IntegerField(null = True, blank= True)
    created_at = models.DateTimeField(auto_now_add= True)

class Loan(models.Model):
    LOAN_STATUS = [
        ('ACTIVE','active'),
        ('CLOSED','closed'),
    ]
    user = models.ForeignKey( User, on_delete = models.CASCADE )
    loan_type = models.CharField( max_length = 50, default = 'CREDIT CARD' )
    loan_amount = models.DecimalField( max_digits = 10, decimal_places = 2 )
    interest_rate = models.DecimalField( max_digits = 5, decimal_places = 2 )
    term_period = models.IntegerField()
    disbursement_date = models.DateField()
    status = models.CharField( max_length = 10, choices = LOAN_STATUS , default = 'ACTIVE' )
    created_at = models.DateTimeField( auto_now_add = True )

class Payment(models.Model):
    loan = models.ForeignKey( Loan, on_delete=models.CASCADE )
    amount = models.DecimalField( max_digits = 10, decimal_places= 2 )
    payment_date = models.DateField( default = timezone.now )
    created_at = models.DateTimeField( auto_now_add = True )

class Billing(models.Model):
    loan = models.ForeignKey( Loan, on_delete = models.CASCADE )
    billing_date = models.DateField()
    due_date = models.DateField()
    min_due = models.DecimalField( max_digits = 10, decimal_places= 2)
    principal_due = models.DecimalField( max_digits = 10, decimal_places = 2)
    interest_due = models.DecimalField(max_digits=10 , decimal_places= 2)
    created_at = models.DateTimeField(auto_now_add = True )
