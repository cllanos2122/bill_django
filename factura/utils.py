# apps/factura/utils.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
import os
from django.conf import settings
from .models import Empresa

def get_empresa_info(user):
    """Obtiene la información de la empresa del usuario"""
    try:
        empresa = Empresa.objects.get(usuario=user)
        return {
            'nombre': empresa.nombre,
            'nit': empresa.nit,
            'direccion': empresa.direccion,
            'telefono': empresa.telefono,
            'email': empresa.email,
            'logo_path': empresa.logo.path if empresa.logo else None
        }
    except Empresa.DoesNotExist:
        return {
            'nombre': "EMPRESA XYZ LTDA",
            'nit': "901.234.567-8",
            'direccion': "Calle 123 #45-67, Bogotá, Colombia",
            'telefono': "+57 300 123 4567",
            'email': "facturacion@empresa.com",
            'logo_path': None
        }

def render_pdf_factura(buffer, factura):
    elements = []
    styles = getSampleStyleSheet()
    
    # Obtener info de la empresa
    empresa_info = get_empresa_info(factura.creado_por)
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=20,
        alignment=1  # Centrado
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.HexColor('#2c3e50')
    )
    
    normal_bold = ParagraphStyle(
        'NormalBold',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold'
    )
    
    normal_right = ParagraphStyle(
        'NormalRight',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT
    )
    
    normal_bold_right = ParagraphStyle(
        'NormalBoldRight',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT
    )

    # Logo
    try:
        if empresa_info['logo_path'] and os.path.exists(empresa_info['logo_path']):
            logo = Image(empresa_info['logo_path'], width=1.5*inch, height=0.8*inch)
            elements.append(logo)
            elements.append(Spacer(1, 10))
    except:
        pass

    # Información de la empresa
    elements.append(Paragraph(empresa_info['nombre'], header_style))
    elements.append(Paragraph(f"NIT: {empresa_info['nit']}", styles['Normal']))
    elements.append(Paragraph(empresa_info['direccion'], styles['Normal']))
    elements.append(Paragraph(f"Teléfono: {empresa_info['telefono']}", styles['Normal']))
    elements.append(Paragraph(f"Email: {empresa_info['email']}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Título de la factura
    elements.append(Paragraph("FACTURA DE VENTA", title_style))
    elements.append(Paragraph(f"No. {factura.id}", title_style))
    elements.append(Spacer(1, 20))

    # Información del cliente (izquierda) y fecha/estado (derecha)
    cliente_data = [
        [Paragraph("<b>Cliente:</b>", normal_bold), Paragraph(factura.cliente.nombre, styles['Normal'])],
        [Paragraph("<b>Documento:</b>", normal_bold), Paragraph(factura.cliente.documento_identidad or "No especificado", styles['Normal'])],
        [Paragraph("<b>Email:</b>", normal_bold), Paragraph(factura.cliente.email or "No especificado", styles['Normal'])],
        [Paragraph("<b>Teléfono:</b>", normal_bold), Paragraph(factura.cliente.telefono or "No especificado", styles['Normal'])],
        [Paragraph("<b>Dirección:</b>", normal_bold), Paragraph(factura.cliente.direccion or "No especificada", styles['Normal'])],
    ]
    
    fecha_data = [
        [Paragraph("<b>Fecha:</b>", normal_bold), Paragraph(factura.fecha.strftime('%d/%m/%Y %H:%M'), styles['Normal'])],
        [Paragraph("<b>Estado:</b>", normal_bold), Paragraph(factura.get_estado_display(), styles['Normal'])],
    ]
    
    from reportlab.platypus import Table
    cliente_table = Table(cliente_data, colWidths=[80, 300])
    fecha_table = Table(fecha_data, colWidths=[80, 120])
    
    # Combinar ambas tablas en una fila
    combined_data = [[cliente_table, fecha_table]]
    combined_table = Table(combined_data, colWidths=[380, 200])
    combined_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(combined_table)
    elements.append(Spacer(1, 20))

    # Tabla de productos
    product_headers = ['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']
    product_data = [product_headers]
    
    for detalle in factura.detalles.all():
        product_data.append([
            detalle.producto.nombre,
            str(detalle.cantidad),
            f"${detalle.precio_unitario:,.2f}",
            f"${detalle.subtotal:,.2f}"
        ])
    
    product_table = Table(product_data, colWidths=[200, 60, 80, 80])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(product_table)
    elements.append(Spacer(1, 15))

    # Totales (alineados a la derecha)
    totals_data = []
    
    totals_data.append([
        Paragraph("Subtotal:", normal_bold),
        Paragraph(f"${factura.subtotal:,.2f}", normal_bold_right)
    ])
    
    if factura.iva_valor > 0:
        totals_data.append([
            Paragraph(f"IVA ({factura.iva_porcentaje}%)", normal_bold),
            Paragraph(f"${factura.iva_valor:,.2f}", normal_bold_right)
        ])
    
    if factura.imp_consumo_valor > 0:
        totals_data.append([
            Paragraph(f"Imp. Consumo ({factura.imp_consumo_porcentaje}%)", normal_bold),
            Paragraph(f"${factura.imp_consumo_valor:,.2f}", normal_bold_right)
        ])
    
    if factura.retefuente_valor > 0:
        totals_data.append([
            Paragraph(f"Retefuente ({factura.retefuente_porcentaje}%)", normal_bold),
            Paragraph(f"-${factura.retefuente_valor:,.2f}", normal_bold_right)
        ])
    
    totals_data.append([
        Paragraph("TOTAL:", normal_bold),
        Paragraph(f"${factura.total_con_impuestos:,.2f}", normal_bold_right)
    ])
    
    totals_table = Table(totals_data, colWidths=[300, 100])
    totals_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # Términos y condiciones
    terminos_style = ParagraphStyle(
        'TerminosStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    terminos = """
    <b>TÉRMINOS Y CONDICIONES:</b><br/>
    • Esta factura es válida por 30 días calendario.<br/>
    • Los pagos deben realizarse en la cuenta bancaria especificada.<br/>
    • Factura sujeta a retención en la fuente según normativa vigente.<br/>
    • Resolución DIAN No. 12345 del 01/01/2023.<br/>
    • Validación en: www.dian.gov.co
    """
    elements.append(Paragraph(terminos, terminos_style))
    elements.append(Spacer(1, 15))

    # Pie de página
    elements.append(Paragraph("Gracias por su preferencia!", styles['Normal']))
    elements.append(Paragraph(f"www.{empresa_info['nombre'].lower().replace(' ', '')}.com | {empresa_info['email']}", terminos_style))

    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build(elements)






# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib.units import inch
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# import os
# from django.conf import settings

# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import inch
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# import os
# from django.conf import settings


# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import inch
# from reportlab.pdfbase import pdfmetrics
# from reportlab.lib.enums import TA_RIGHT, TA_LEFT
# import os
# from django.conf import settings
# from .models import Empresa

# def get_empresa_info(user):
#     totals_data.append([
#         Paragraph("Subtotal:", normal_bold),
#         Paragraph(f"${factura.subtotal:,.2f}", normal_bold_right)
#     ])
    
#     if factura.iva_valor > 0:
#         totals_data.append([
#             Paragraph(f"IVA ({factura.iva_porcentaje}%)", normal_bold),
#             Paragraph(f"${factura.iva_valor:,.2f}", normal_bold_right)
#         ])
    
#     if factura.imp_consumo_valor > 0:
#         totals_data.append([
#             Paragraph(f"Imp. Consumo ({factura.imp_consumo_porcentaje}%)", normal_bold),
#             Paragraph(f"${factura.imp_consumo_valor:,.2f}", normal_bold_right)
#         ])
    
#     if factura.retefuente_valor > 0:
#         totals_data.append([
#             Paragraph(f"Retefuente ({factura.retefuente_porcentaje}%)", normal_bold),
#             Paragraph(f"-${factura.retefuente_valor:,.2f}", normal_bold_right)
#         ])
    
#     totals_data.append([
#         Paragraph("TOTAL:", normal_bold),
#         Paragraph(f"${factura.total_con_impuestos:,.2f}", normal_bold_right)
#     ])
    
#     totals_table = Table(totals_data, colWidths=[300, 100])
#     totals_table.setStyle(TableStyle([
#         ('TOPPADDING', (0, 0), (-1, -1), 6),
#         ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
#     ]))
#     elements.append(totals_table)
#     elements.append(Spacer(1, 20))

#     # Términos y condiciones
#     terminos_style = ParagraphStyle(
#         'TerminosStyle',
#         parent=styles['Normal'],
#         fontSize=9,
#         textColor=colors.HexColor('#7f8c8d')
#     )
    
#     terminos = """
#     <b>TÉRMINOS Y CONDICIONES:</b><br/>
#     • Esta factura es válida por 30 días calendario.<br/>
#     • Los pagos deben realizarse en la cuenta bancaria especificada.<br/>
#     • Factura sujeta a retención en la fuente según normativa vigente.<br/>
#     • Resolución DIAN No. 12345 del 01/01/2023.<br/>
#     • Validación en: www.dian.gov.co
#     """
#     elements.append(Paragraph(terminos, terminos_style))
#     elements.append(Spacer(1, 15))

#     # Pie de página
#     elements.append(Paragraph("Gracias por su preferencia!", styles['Normal']))
#     elements.append(Paragraph(f"www.{empresa_info['nombre'].lower().replace(' ', '')}.com | {empresa_info['email']}", terminos_style))

#     doc = SimpleDocTemplate(buffer, pagesize=letter)
#     doc.build(elements)


# =============================================================================
# def render_pdf_factura(buffer, factura):
#     doc = SimpleDocTemplate(buffer, pagesize=letter)
#     elements = []
#     styles = getSampleStyleSheet()
#     
#     # Estilo personalizado para el encabezado
#     header_style = ParagraphStyle(
#         'CustomHeader',
#         parent=styles['Heading1'],
#         fontSize=16,
#         spaceAfter=10,
#         textColor=colors.HexColor('#2c3e50')
#     )
#     
#     # Estilo para información de empresa
#     info_style = ParagraphStyle(
#         'InfoStyle',
#         parent=styles['Normal'],
#         fontSize=10,
#         textColor=colors.HexColor('#7f8c8d')
#     )
# 
#     # Logo de la empresa (opcional)
#     logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo_empresa.png')
#     if os.path.exists(logo_path):
#         try:
#             logo = Image(logo_path, width=1.5*inch, height=0.8*inch)
#             elements.append(logo)
#             elements.append(Spacer(1, 12))
#         except:
#             pass  # Si hay error con el logo, lo omitimos
# 
#     # Información de la empresa
#     elements.append(Paragraph("EMPRESA XYZ LTDA", header_style))
#     elements.append(Paragraph("NIT: 901.234.567-8", info_style))
#     elements.append(Paragraph("Dirección: Calle 123 #45-67, Bogotá, Colombia", info_style))
#     elements.append(Paragraph("Teléfono: +57 300 123 4567", info_style))
#     elements.append(Paragraph("Email: facturacion@empresa.com", info_style))
#     elements.append(Spacer(1, 20))
# 
#     # Título de la factura
#     elements.append(Paragraph(f"<b>FACTURA DE VENTA</b>", styles['Title']))
#     elements.append(Paragraph(f"<b>No. {factura.id}</b>", styles['Title']))
#     elements.append(Spacer(1, 20))
# 
#     # Información del cliente
#     cliente_info = f"""
#     <b>Cliente:</b> {factura.cliente.nombre}<br/>
#     <b>Documento:</b> {factura.cliente.documento_identidad or 'No especificado'}<br/>
#     <b>Email:</b> {factura.cliente.email or 'No especificado'}<br/>
#     <b>Teléfono:</b> {factura.cliente.telefono or 'No especificado'}<br/>
#     <b>Dirección:</b> {factura.cliente.direccion or 'No especificada'}
#     """
#     elements.append(Paragraph(cliente_info, styles['Normal']))
#     elements.append(Spacer(1, 20))
# 
#     # Fecha y estado
#     elements.append(Paragraph(f"<b>Fecha:</b> {factura.fecha.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
#     elements.append(Paragraph(f"<b>Estado:</b> {factura.get_estado_display()}", styles['Normal']))
#     elements.append(Spacer(1, 20))
# 
#     # Tabla de productos
#     data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
#     for detalle in factura.detalles.all():
#         data.append([
#             detalle.producto.nombre,
#             str(detalle.cantidad),
#             f"${detalle.precio_unitario:,.2f}",
#             f"${detalle.subtotal:,.2f}"
#         ])
#     
#     # Totales
#     data.append(['', '', '<b>Subtotal:</b>', f"<b>${factura.subtotal:,.2f}</b>"])
#     if factura.iva_valor > 0:
#         data.append(['', '', f"<b>IVA ({factura.iva_porcentaje}%)</b>:", f"<b>${factura.iva_valor:,.2f}</b>"])
#     if factura.imp_consumo_valor > 0:
#         data.append(['', '', f"<b>Imp. Consumo ({factura.imp_consumo_porcentaje}%)</b>:", f"<b>${factura.imp_consumo_valor:,.2f}</b>"])
#     if factura.retefuente_valor > 0:
#         data.append(['', '', f"<b>Retefuente ({factura.retefuente_porcentaje}%)</b>:", f"<b>-${factura.retefuente_valor:,.2f}</b>"])
#     data.append(['', '', '<b>TOTAL:</b>', f"<b>${factura.total_con_impuestos:,.2f}</b>"])
# 
#     # Estilo de tabla
#     table = Table(data, colWidths=[200, 60, 80, 80])
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, 0), 10),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#ecf0f1')),
#         ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#27ae60')),
#         ('TEXTCOLOR', (-2, -1), (-1, -1), colors.whitesmoke),
#         ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
#         ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     ]))
#     elements.append(table)
#     elements.append(Spacer(1, 20))
# 
#     # Términos y condiciones
#     terminos = """
#     <b>TÉRMINOS Y CONDICIONES:</b><br/>
#     • Esta factura es válida por 30 días calendario.<br/>
#     • Los pagos deben realizarse en la cuenta bancaria especificada.<br/>
#     • Factura sujeta a retención en la fuente según normativa vigente.<br/>
#     • Resolución DIAN No. 12345 del 01/01/2023.<br/>
#     • Validación en: www.dian.gov.co
#     """
#     elements.append(Paragraph(terminos, styles['Normal']))
#     elements.append(Spacer(1, 20))
# 
#     # Pie de página
#     elements.append(Paragraph("Gracias por su preferencia!", styles['Normal']))
#     elements.append(Paragraph("www.empresa.com | facturacion@empresa.com", info_style))
# 
#     doc.build(elements)
# 
# 
# =============================================================================
# =============================================================================
# def render_pdf_factura(buffer, factura):
#     doc = SimpleDocTemplate(buffer, pagesize=letter)
#     elements = []
#     styles = getSampleStyleSheet()
# 
#     # Título
#     elements.append(Paragraph(f"Factura #{factura.id}", styles['Title']))
#     elements.append(Spacer(1, 12))
# 
#     # Datos del cliente
#     elements.append(Paragraph(f"Cliente: {factura.cliente.nombre}", styles['Normal']))
#     if factura.cliente.email:
#         elements.append(Paragraph(f"Email: {factura.cliente.email}", styles['Normal']))
#     elements.append(Paragraph(f"Fecha: {factura.fecha.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
#     elements.append(Paragraph(f"Estado: {factura.get_estado_display()}", styles['Normal']))
#     elements.append(Spacer(1, 12))
# 
#     # Tabla de productos
#     data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
#     for detalle in factura.detalles.all():
#         data.append([
#             detalle.producto.nombre,
#             str(detalle.cantidad),
#             f"${detalle.precio_unitario}",
#             f"${detalle.subtotal}"
#         ])
#     
#     # Totales
#     data.append(['', '', 'Subtotal:', f"${factura.subtotal}"])
#     if factura.iva_valor > 0:
#         data.append(['', '', f"IVA ({factura.iva_porcentaje}%):", f"${factura.iva_valor}"])
#     if factura.imp_consumo_valor > 0:
#         data.append(['', '', f"Imp. Consumo ({factura.imp_consumo_porcentaje}%):", f"${factura.imp_consumo_valor}"])
#     if factura.retefuente_valor > 0:
#         data.append(['', '', f"Retefuente ({factura.retefuente_porcentaje}%):", f"-${factura.retefuente_valor}"])
#     data.append(['', '', 'Total:', f"${factura.total_con_impuestos}"])
# 
#     # Estilo de tabla
#     table = Table(data)
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, 0), 10),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#     ]))
#     elements.append(table)
# 
#     doc.build(elements)
# =============================================================================


# =============================================================================
# def render_pdf_factura(response, factura):
#     doc = SimpleDocTemplate(response, pagesize=letter)
#     elements = []
#     styles = getSampleStyleSheet()
# 
#     # Título
#     elements.append(Paragraph(f"Factura #{factura.id}", styles['Title']))
#     elements.append(Spacer(1, 12))
# 
#     # Datos del cliente
#     elements.append(Paragraph(f"Cliente: {factura.cliente.nombre}", styles['Normal']))
#     elements.append(Paragraph(f"Fecha: {factura.fecha.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
#     elements.append(Paragraph(f"Estado: {factura.get_estado_display()}", styles['Normal']))
#     elements.append(Spacer(1, 12))
# 
#     # Tabla de productos
#     data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
#     for detalle in factura.detalles.all():
#         data.append([
#             detalle.producto.nombre,
#             str(detalle.cantidad),
#             f"${detalle.precio_unitario}",
#             f"${detalle.subtotal}"
#         ])
#     data.append(['', '', 'Total:', f"${factura.total}"])
# 
#     table = Table(data)
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, 0), 12),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#     ]))
#     elements.append(table)
# 
#     doc.build(elements)
# =============================================================================
