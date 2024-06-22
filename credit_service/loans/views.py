from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, Loan, Payment, Billing
from .serializers import UserSerializer, LoanSerializer, PaymentSerializer
from django.utils import timezone
from .tasks import calculate_credit_score

# Create your views here.

class RegisterUserView(APIView):
    def post(self,request):
        serializer = UserSerializer(data = request.data)
        if serializer.is_valid():
            user = serializer.save()
            calculate_credit_score.delay(user.id)
            return Response({'Unique_user_id': user.id,'Credit_Score': user.credit_score}, status = status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

class ApplyLoanView(APIView):
    def post(self, request):
        serializer = LoanSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            if user.credit_score < 450:
                return Response({'error': 'Credit score too low'}, status=status.HTTP_400_BAD_REQUEST)
            if user.annual_income < 150000:
                return Response({'error': 'Annual income too low'}, status=status.HTTP_400_BAD_REQUEST)
            if serializer.validated_data['loan_amount'] > 5000:
                return Response({'error': 'Loan amount exceeds limit'}, status=status.HTTP_400_BAD_REQUEST)
            loan = serializer.save()
            self.create_billing_schedule(loan)
            return Response({'loan_id': loan.id}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create_billing_schedule(self, loan):
        disbursement_date = loan.disbursement_date
        for month in range(loan.term_period):
            billing_date = disbursement_date + timezone.timedelta(days=30 * month)
            due_date = billing_date + timezone.timedelta(days=15)
            min_due = self.calculate_min_due(loan.loan_amount, loan.interest_rate)
            Billing.objects.create(
                loan=loan,
                billing_date=billing_date,
                due_date=due_date,
                min_due=min_due
            )

    def calculate_min_due(self, principal, interest_rate):
        daily_apr = round(interest_rate / 365, 3)
        min_due = (principal * 0.03) + (daily_apr * principal * 30)
        return round(min_due, 2)
    

class MakePaymentView(APIView):
    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save()
            self.update_loan_status(payment.loan)
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_loan_status(self, loan):
        payments = Payment.objects.filter(loan=loan)
        total_paid = sum(payment.amount for payment in payments)
        billing_records = Billing.objects.filter(loan=loan).order_by('billing_date')

        for billing in billing_records:
            if billing.past_due > 0:
                if total_paid >= billing.past_due:
                    total_paid -= billing.past_due
                    billing.past_due = 0
                else:
                    billing.past_due -= total_paid
                    total_paid = 0
                    break

            if total_paid >= billing.min_due:
                total_paid -= billing.min_due
                billing.min_due = 0
            else:
                billing.past_due += billing.min_due - total_paid
                total_paid = 0
                break

            billing.save()

        if total_paid > 0:
            remaining_principal = max(loan.loan_amount - total_paid, 0)
            loan.loan_amount = remaining_principal
            loan.save()

            if remaining_principal == 0:
                loan.status = 'closed'
                loan.save()


class GetStatementView(APIView):
    def get(self, request):
        loan_id = request.query_params.get('loan_id')
        try:
            loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_400_BAD_REQUEST)

        past_transactions = []
        upcoming_transactions = []

        billing_records = Billing.objects.filter(loan=loan).order_by('billing_date')
        payments = Payment.objects.filter(loan=loan).order_by('payment_date')

        for billing in billing_records:
            past_transactions.append({
                'date': billing.billing_date,
                'principal': loan.loan_amount,
                'interest': self.calculate_interest(loan.loan_amount, loan.interest_rate, billing.billing_date),
                'amount_paid': sum(payment.amount for payment in payments if payment.payment_date <= billing.due_date)
            })
            upcoming_transactions.append({
                'date': billing.due_date,
                'amount_due': billing.min_due + billing.past_due
            })

        return Response({
            'past_transactions': past_transactions,
            'upcoming_transactions': upcoming_transactions
        }, status=status.HTTP_200_OK)

    def calculate_interest(self, principal, interest_rate, billing_date):
        daily_apr = round(interest_rate / 365, 3)
        days = (timezone.now().date() - billing_date).days
        interest = daily_apr * principal * days
        return round(interest, 2)
