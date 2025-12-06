# apps/bill/factura/xml_generator.py

from lxml import etree
from decimal import Decimal
from datetime import datetime

def generar_factura_xml(factura):
    """
    Genera XML de factura electrónica según estándar DIAN (UBL 2.1)
    """
    # Namespace UBL
    nsmap = {
        None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    }
    
    # Raíz del documento
    invoice = etree.Element("Invoice", nsmap=nsmap)
    
    # Información básica
    etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}UBLVersionID").text = "2.1"
    etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = str(factura.id)
    etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate").text = factura.fecha.strftime("%Y-%m-%d")
    etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode").text = "01"  # Factura electrónica
    
    # Moneda
    etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}DocumentCurrencyCode").text = "COP"
    
    # Información del vendedor (empresa)
    try:
        from .models import Empresa
        empresa = Empresa.objects.get(usuario=factura.creado_por)
        seller = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
        party = etree.SubElement(seller, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        party_name = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
        etree.SubElement(party_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = empresa.nombre
        
        # Identificación del vendedor
        party_identification = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification")
        etree.SubElement(party_identification, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID", 
                        schemeID="4").text = empresa.nit.replace("-", "").replace(".", "")
    except:
        # Datos por defecto si no hay empresa configurada
        seller = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
        party = etree.SubElement(seller, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
        party_name = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
        etree.SubElement(party_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = "EMPRESA XYZ LTDA"
        
        party_identification = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification")
        etree.SubElement(party_identification, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID", 
                        schemeID="4").text = "9012345678"
    
    # Información del comprador (cliente)
    buyer = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty")
    party = etree.SubElement(buyer, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party")
    party_name = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
    etree.SubElement(party_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name").text = factura.cliente.nombre
    
    # Identificación del cliente
    if factura.cliente.documento_identidad:
        doc_clean = factura.cliente.documento_identidad.replace("-", "").replace(".", "")
        if doc_clean.isdigit():
            scheme_id = "31" if len(doc_clean) == 10 else "13"  # NIT o CC
        else:
            scheme_id = "13"
    else:
        doc_clean = "222222222222"
        scheme_id = "13"
    
    party_identification = etree.SubElement(party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification")
    etree.SubElement(party_identification, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID", 
                    schemeID=scheme_id).text = doc_clean
    
    # Total antes de impuestos
    legal_monetary_total = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal")
    etree.SubElement(legal_monetary_total, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount", 
                    currencyID="COP").text = str(factura.total_con_impuestos)
    
    # Ítems de la factura
    for i, detalle in enumerate(factura.detalles.all(), 1):
        invoice_line = etree.SubElement(invoice, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceLine")
        etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID").text = str(i)
        etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoicedQuantity", 
                        unitCode="EA").text = str(detalle.cantidad)
        etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount", 
                        currencyID="COP").text = str(detalle.subtotal)
        
        # Información del producto
        item = etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Item")
        etree.SubElement(item, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Description").text = detalle.producto.nombre
        
        # Precio
        price = etree.SubElement(invoice_line, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Price")
        etree.SubElement(price, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PriceAmount", 
                        currencyID="COP").text = str(detalle.precio_unitario)
    
    return etree.tostring(invoice, pretty_print=True, xml_declaration=True, encoding='UTF-8')