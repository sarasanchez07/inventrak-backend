from django.urls import path
from apps.reports.views.reports_views import MovementReportAPIView

urlpatterns = [
    path('movements/', MovementReportAPIView.as_view(), name='report-movements'),
]