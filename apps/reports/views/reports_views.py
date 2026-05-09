from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.reports.services.reports_services import ReportService
from apps.reports.serializers.reports_serializers import ReportMovementSerializer
from ..utils.export_strategies import CSVExportStrategy, PDFExportStrategy

class MovementReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        m_type = request.query_params.get('type')
        inv_id = request.query_params.get('inventory_id')
        prod_id = request.query_params.get('product_id')
        format_type = request.query_params.get('export')

        # Obtener data filtrada desde el servicio
        movements = ReportService.get_filtered_movements(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            movement_type=m_type,
            inventory_id=inv_id,
            product_id=prod_id
        )

        # Manejar exportaciones
        if format_type == 'csv':
            return CSVExportStrategy().export(movements, "reporte_inventario")
        elif format_type == 'pdf':
            return PDFExportStrategy().export(movements, "reporte_inventario")

        # Respuesta JSON estándar
        serializer = ReportMovementSerializer(movements, many=True)
        return Response(serializer.data)