from rest_framework import serializers
from .models import User, Loan, Payment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['aadhar_id','name','email','annual_income','credit_score']

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['user','loan_type','loan_amount','interest_rate','term_period','term_period','disbursement_date']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['loan','amount']