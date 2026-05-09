from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..services.alert_service import AlertService
from ..serializers.alert_serializers import AlertSerializer
from ..models import Alert
from django.shortcuts import get_object_or_404

class AlertListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventory_id = request.query_params.get('inventory_id')
        alerts = AlertService.get_dynamic_alerts(request.user, inventory_id=inventory_id)
        return Response(alerts)
