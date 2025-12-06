# apps/factura/utils.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import qrcode
import qrcode.image.svg
from io import BytesIO
import os
from django.conf import settings

# Soporte multilingüe
TRANSLATIONS = {
    'es': {
        'invoice': 'FACTURA DE VENTA',
        'no': 'No.',
        'client': 'Cliente',
        'document': 'Documento',
        'email': 'Email',
        'phone': 'Teléfono',
        'address': 'Dirección',
        'date': 'Fecha',
        'status': 'Estado',
        'product': 'Producto',
        'quantity': 'Cantidad',
        'unit_price': 'Precio Unit.',
        'subtotal': 'Subtotal',
        'iva': 'IVA',
        'consumption_tax': 'Imp. Consumo',
        'withholding': 'Retefuente',
        'total': 'TOTAL',
        'terms': 'TÉRMINOS Y CONDICIONES',
        'validity': '• Esta factura es válida por 30 días calendario.',
        'payment': '• Los pagos deben realizarse en la cuenta bancaria especificada.',
        'withholding_note': '• Factura sujeta a retención en la fuente según normativa vigente.',
        'resolution': '• Resolución DIAN No. 12345 del 01/01/2023.',
        'validation': '• Validación en: www.dian.gov.co',
        'thanks': 'Gracias por su preferencia!',
        'not_specified': 'No especificado',
        'not_specified_f': 'No especificada'
    },
    'en': {
        'invoice': 'SALES INVOICE',
        'no': 'No.',
        'client': 'Client',
        'document': 'Document',
        'email': 'Email',
        'phone': 'Phone',
        'address': 'Address',
        'date': 'Date',
        'status': 'Status',
        'product': 'Product',
        'quantity': 'Quantity',
        'unit_price': 'Unit Price',
        'subtotal': 'Subtotal',
        'iva': 'VAT',
        'consumption_tax': 'Consumption Tax',
        'withholding': 'Withholding Tax',
        'total': 'TOTAL',
        'terms': 'TERMS AND CONDITIONS',
        'validity': '• This invoice is valid for 30 calendar days.',
        'payment': '• Payments must be made to the specified bank account.',
        'withholding_note': '• Invoice subject to withholding tax according to current regulations.',
        'resolution': '• DIAN Resolution No. 12345 of 01/01/2023.',
        'validation': '• Validation at: www.dian.gov.co',
        'thanks': 'Thank you for your preference!',
        'not_specified': 'Not specified',
        'not_specified_f': 'Not specified'
    }
}

def generate_qr_code(factura):
    """Genera un código QR con los datos de la factura"""
    qr_data = f"""
    Factura: {factura.id}
    Cliente: {factura.cliente.nombre}
    Documento: {factura.cliente.documento_identidad or 'N/A'}
    Total: ${factura.total_con_impuestos}
    Fecha: {factura.fecha.strftime('%Y-%m-%d')}
    """
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a bytes para ReportLab
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

def render_pdf_factura(buffer, factura, language='es'):
    elements = []
    styles = getSampleStyleSheet()
    tr = TRANSLATIONS.get(language, TRANSLATIONS['es'])
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
        textColor=colors.HexColor('#2c3e50')
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d')
    )

    # Logo
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo_empresa.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=1.5*inch, height=0.8*inch)
            elements.append(logo)
            elements.append(Spacer(1, 12))
    except:
        pass

    # Información de la empresa
    elements.append(Paragraph("EMPRESA XYZ LTDA", header_style))
    elements.append(Paragraph("NIT: 901.234.567-8", info_style))
    elements.append(Paragraph("Dirección: Calle 123 #45-67, Bogotá, Colombia", info_style))
    elements.append(Paragraph("Teléfono: +57 300 123 4567", info_style))
    elements.append(Paragraph("Email: facturacion@empresa.com", info_style))
    elements.append(Spacer(1, 20))

    # Título
    elements.append(Paragraph(f"<b>{tr['invoice']}</b>", styles['Title']))
    elements.append(Paragraph(f"<b>{tr['no']} {factura.id}</b>", styles['Title']))
    elements.append(Spacer(1, 20))

    # Cliente
    cliente_info = f"""
    <b>{tr['client']}:</b> {factura.cliente.nombre}<br/>
    <b>{tr['document']}:</b> {factura.cliente.documento_identidad or tr['not_specified']}<br/>
    <b>{tr['email']}:</b> {factura.cliente.email or tr['not_specified']}<br/>
    <b>{tr['phone']}:</b> {factura.cliente.telefono or tr['not_specified']}<br/>
    <b>{tr['address']}:</b> {factura.cliente.direccion or tr['not_specified_f']}
    """
    elements.append(Paragraph(cliente_info, styles['Normal']))
    elements.append(Spacer(1, 20))

    # Fecha y estado
    elements.append(Paragraph(f"<b>{tr['date']}:</b> {factura.fecha.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Paragraph(f"<b>{tr['status']}:</b> {factura.get_estado_display()}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Productos
    data = [[tr['product'], tr['quantity'], tr['unit_price'], tr['subtotal']]]
    for detalle in factura.detalles.all():
        data.append([
            detalle.producto.nombre,
            str(detalle.cantidad),
            f"${detalle.precio_unitario:,.2f}",
            f"${detalle.subtotal:,.2f}"
        ])
    
    # Totales
    data.append(['', '', f"<b>{tr['subtotal']}:</b>", f"<b>${factura.subtotal:,.2f}</b>"])
    if factura.iva_valor > 0:
        data.append(['', '', f"<b>{tr['iva']} ({factura.iva_porcentaje}%)</b>:", f"<b>${factura.iva_valor:,.2f}</b>"])
    if factura.imp_consumo_valor > 0:
        data.append(['', '', f"<b>{tr['consumption_tax']} ({factura.imp_consumo_porcentaje}%)</b>:", f"<b>${factura.imp_consumo_valor:,.2f}</b>"])
    if factura.retefuente_valor > 0:
        data.append(['', '', f"<b>{tr['withholding']} ({factura.retefuente_porcentaje}%)</b>:", f"<b>-${factura.retefuente_valor:,.2f}</b>"])
    data.append(['', '', f"<b>{tr['total']}:</b>", f"<b>${factura.total_con_impuestos:,.2f}</b>"])

    table = Table(data, colWidths=[200, 60, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#ecf0f1')),
        ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (-2, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Código QR
    try:
        qr_buffer = generate_qr_code(factura)
        qr_img = Image(qr_buffer, width=1.2*inch, height=1.2*inch)
        elements.append(qr_img)
        elements.append(Spacer(1, 10))
    except:
        pass

    # Términos
    terminos = f"""
    <b>{tr['terms']}:</b><br/>
    {tr['validity']}<br/>
    {tr['payment']}<br/>
    {tr['withholding_note']}<br/>
    {tr['resolution']}<br/>
    {tr['validation']}
    """
    elements.append(Paragraph(terminos, styles['Normal']))
    elements.append(Spacer(1, 20))

    # Pie
    elements.append(Paragraph(tr['thanks'], styles['Normal']))
    elements.append(Paragraph("www.empresa.com | facturacion@empresa.com", info_style))

    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build(elements)