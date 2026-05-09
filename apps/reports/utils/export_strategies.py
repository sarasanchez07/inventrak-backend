import csv
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class ExportStrategy:
    def export(self, queryset, filename):
        raise NotImplementedError

class CSVExportStrategy(ExportStrategy):
    def export(self, queryset, filename):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        response.write('\ufeff') # Agrega BOM para que Excel detecte UTF-8
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Fecha', 'Producto', 'Inventario', 'Tipo', 'Cantidad', 'Stock Resultante', 'Motivo', 'Personal'])
        for m in queryset:
            inv_name = m.product.inventory.name if m.product and hasattr(m.product, 'inventory') and m.product.inventory else "N/A"
            movement_type = "Entrada" if m.type == "IN" else "Salida"
            date_formatted = m.created_at.strftime('%d/%m/%Y')
            
            # Formato de stock (usamos el histórico si existe)
            stock_display = "N/A"
            if m.product:
                stock_display = m.product.get_stock_display(custom_stock=m.resulting_stock)
            
            writer.writerow([date_formatted, m.product_name_at_time, inv_name, movement_type, m.quantity, stock_display, m.reason, m.user.email if m.user else "Sistema"])
        return response

class PDFExportStrategy(ExportStrategy):
    def export(self, queryset, filename):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        p = canvas.Canvas(response, pagesize=letter)
        y = 750
        p.drawString(100, y, "Reporte de Movimientos InvenTrack")
        y -= 40
        p.drawString(50, y, "Fecha | Producto | Tipo | Cant | Stock | Usuario")
        y -= 20
        p.line(50, y+15, 550, y+15)
        
        for m in queryset:
            stock_display = "N/A"
            if m.product:
                stock_display = m.product.get_stock_display(custom_stock=m.resulting_stock)
                
            line = f"{m.created_at.date()} | {m.product_name_at_time[:15]} | {m.type} | {m.quantity} | {stock_display} | {m.user.email if m.user else 'Sys'}"
            p.drawString(50, y, line)
            y -= 20
            if y < 50: p.showPage(); y = 750
        p.save()
        return response