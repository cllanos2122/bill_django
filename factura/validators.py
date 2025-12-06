# apps/bill/factura/validators.py

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validar_documento_colombiano(value):
    """
    Valida documentos de identidad colombianos:
    - Cédula de Ciudadanía (CC): 6-10 dígitos
    - Cédula de Extranjería (CE): 6-12 dígitos
    - NIT: 9-10 dígitos + dígito de verificación
    - Pasaporte: Alfanumérico, 5-20 caracteres
    """
    if not value:
        return
    
    # Remover caracteres especiales
    clean_value = re.sub(r'[^\w]', '', value.upper())
    
    # Detectar tipo de documento
    if re.match(r'^CC\d{6,10}$', value.upper()) or re.match(r'^\d{6,10}$', clean_value):
        # Cédula de Ciudadanía
        if len(clean_value) < 6 or len(clean_value) > 10:
            raise ValidationError(
                _('La Cédula de Ciudadanía debe tener entre 6 y 10 dígitos.'),
                code='invalid_cc'
            )
        if not clean_value.isdigit():
            raise ValidationError(
                _('La Cédula de Ciudadanía solo puede contener números.'),
                code='invalid_cc'
            )
            
    elif re.match(r'^CE\d{6,12}$', value.upper()) or (clean_value.isdigit() and 6 <= len(clean_value) <= 12):
        # Cédula de Extranjería
        if len(clean_value) < 6 or len(clean_value) > 12:
            raise ValidationError(
                _('La Cédula de Extranjería debe tener entre 6 y 12 dígitos.'),
                code='invalid_ce'
            )
            
    elif re.match(r'^NIT\d{9,10}-?\d?$', value.upper()) or re.match(r'^\d{9,10}-?\d?$', clean_value):
        # NIT con validación de dígito de verificación
        nit_clean = re.sub(r'[^\d]', '', clean_value)
        if len(nit_clean) < 9 or len(nit_clean) > 11:
            raise ValidationError(
                _('El NIT debe tener 9-10 dígitos + dígito de verificación.'),
                code='invalid_nit'
            )
        if not validar_digito_verificacion_nit(nit_clean):
            raise ValidationError(
                _('El dígito de verificación del NIT es inválido.'),
                code='invalid_nit_dv'
            )
            
    elif re.match(r'^PASAPORTE.*', value.upper()) or (not clean_value.isdigit() and 5 <= len(clean_value) <= 20):
        # Pasaporte
        if len(clean_value) < 5 or len(clean_value) > 20:
            raise ValidationError(
                _('El pasaporte debe tener entre 5 y 20 caracteres.'),
                code='invalid_passport'
            )
    else:
        raise ValidationError(
            _('Formato de documento no reconocido. Use: CC-123456789, NIT-901234567-8, CE-123456, PASAPORTE-ABC123'),
            code='invalid_document'
        )

def validar_digito_verificacion_nit(nit):
    """Valida el dígito de verificación del NIT colombiano"""
    if len(nit) < 10:
        return True  # NIT sin DV es aceptable en algunos casos
        
    numero = nit[:-1]
    dv_esperado = int(nit[-1])
    
    # Algoritmo de validación del NIT
    factores = [41, 37, 31, 29, 23, 19, 17, 13, 7, 3]
    suma = 0
    for i, digito in enumerate(reversed(numero)):
        if i < len(factores):
            suma += int(digito) * factores[i]
    
    dv_calculado = (11 - (suma % 11)) % 11
    dv_calculado = 0 if dv_calculado == 11 else dv_calculado
    
    return dv_calculado == dv_esperado