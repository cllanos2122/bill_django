# apps/facturacion_app/forms.py

from django import forms
from .models import Factura, Producto, Cliente, Empresa


# class ClienteForm(forms.ModelForm):
#     class Meta:
#         model = Cliente
#         fields = ['nombre', 'documento_identidad', 'email', 'telefono', 'direccion']
#         widgets = {
#             'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
#             'documento_identidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: CC-123456789'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#             'telefono': forms.TextInput(attrs={'class': 'form-control'}),
#             'direccion': forms.TextInput(attrs={'class': 'form-control'}),
#         }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'tipo_documento', 'documento_identidad', 'email', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'documento_identidad': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: CC-123456789, NIT-901234567-8'
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
        }        

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'nit', 'direccion', 'telefono', 'email', 'logo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nit': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }        
        


class FacturaForm(forms.ModelForm):
    enviar_email = forms.BooleanField(
        required=False,
        label="Enviar factura por email al cliente",
        help_text="Solo si el cliente tiene email registrado"
    )

    class Meta:
        model = Factura
        fields = ['cliente', 'estado', 'enviar_email']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['cliente'].queryset = Cliente.objects.filter(creado_por=user)
            
class FacturaImpuestosForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = [
            'cliente', 'estado',
            'iva_porcentaje', 'imp_consumo_porcentaje', 'retefuente_porcentaje'
        ]
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'iva_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'imp_consumo_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
            'retefuente_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0'
            }),
        }            