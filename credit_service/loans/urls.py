from django.urls import path
from . import views

urlpatterns = [
    path('register-user/', views.RegisterUserView.as_view()),
    path('apply-loan/',views.ApplyLoanView.as_view()),
    path('make-payment', views.MakePaymentView.as_view()),
    path('get-statement',views.GetStatementView.as_view()),
]
