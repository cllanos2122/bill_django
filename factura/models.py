#from django.db import models

# Create your models here.

## Desarrollo de cllanos 2025 - huellitas 



# =============================================================================
# class Cliente(models.Model):
#     nombre = models.CharField(max_length=100)
#     email = models.EmailField(blank=True)
#     telefono = models.CharField(max_length=20, blank=True)
#     direccion = models.TextField(blank=True)
#     creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
#     fecha_creacion = models.DateTimeField(auto_now_add=True)
# 
#     def __str__(self):
#         return self.nombre
# 
# class Producto(models.Model):
#     nombre = models.CharField(max_length=100)
#     descripcion = models.TextField(blank=True)
#     precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
#     creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
#     fecha_creacion = models.DateTimeField(auto_now_add=True)
# 
#     def __str__(self):
#         return f"{self.nombre} - ${self.precio}"
# 
# class Factura(models.Model):
#     ESTADOS = [
#         ('pendiente', 'Pendiente'),
#         ('pagada', 'Pagada'),
#         ('cancelada', 'Cancelada'),
#     ]
#     cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
#     fecha = models.DateTimeField(auto_now_add=True)
#     estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
#     total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
# 
#     def __str__(self):
#         return f"Factura {self.id} - {self.cliente}"
# 
# class DetalleFactura(models.Model):
#     factura = models.ForeignKey(Factura, related_name='detalles', on_delete=models.CASCADE)
#     producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
#     cantidad = models.PositiveIntegerField(default=1)
#     precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
#     subtotal = models.DecimalField(max_digits=12, decimal_places=2)
# 
#     def save(self, *args, **kwargs):
#         self.subtotal = self.cantidad * self.precio_unitario
#         super().save(*args, **kwargs)
#         # Actualiza el total de la factura
#         factura = self.factura
#         factura.total = sum(det.subtotal for det in factura.detalles.all())
#         factura.save(update_fields=['total']) 
# 
# =============================================================================
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from .validators import validar_documento_colombiano


IVA_PORCENTAJE = 19  # 19%


# class Cliente(models.Model):
    
#     nombre = models.CharField(max_length=100)
#     documento_identidad = models.CharField(max_length=20, blank=True)  # ← Nuevo campo
#     email = models.EmailField(blank=True)  # ← necesario para envío
#     telefono = models.CharField(max_length=20, blank=True)
#     direccion = models.TextField(blank=True)
#     creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
#     fecha_creacion = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.nombre


class Cliente(models.Model):
    TIPOS_DOCUMENTO = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('NIT', 'NIT'),
        ('PASAPORTE', 'Pasaporte'),
        ('OTRO', 'Otro'),
    ]
    
    nombre = models.CharField(max_length=100)
    tipo_documento = models.CharField(max_length=10, choices=TIPOS_DOCUMENTO, default='CC')
    documento_identidad = models.CharField(
        max_length=20, 
        blank=True,
        validators=[validar_documento_colombiano]  # ← Validador aplicado
    )
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_documento_display()}: {self.documento_identidad})"

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

class Factura(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    # Campos monetarios base
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Impuestos personalizables (en porcentaje)
    iva_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=21.00)  # 21%
    imp_consumo_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    retefuente_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
   
    # Valores calculados
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    imp_consumo_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    retefuente_valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_con_impuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
   
    # total = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # sin IVA
    # iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # total_con_iva = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # creado_por = models.ForeignKey(User, on_delete=models.CASCADE)

    # def calcular_iva_y_total(self):
    #     self.iva = self.total * (IVA_PORCENTAJE / 100)
    #     self.total_con_iva = self.total + self.iva
    
    def calcular_impuestos(self):
        """Calcula todos los impuestos basados en el subtotal y los porcentajes"""
        from decimal import Decimal
        
        self.iva_valor = (self.subtotal * self.iva_porcentaje) / Decimal('100')
        self.imp_consumo_valor = (self.subtotal * self.imp_consumo_porcentaje) / Decimal('100')
        self.retefuente_valor = (self.subtotal * self.retefuente_porcentaje) / Decimal('100')
        
        # Total = subtotal + IVA + Imp. Consumo - Retefuente
        self.total_con_impuestos = (
            self.subtotal + 
            self.iva_valor + 
            self.imp_consumo_valor - 
            self.retefuente_valor
        )
        
        # Asegurar que no sea negativo
        if self.total_con_impuestos < 0:
            self.total_con_impuestos = Decimal('0.00')

    def save(self, *args, **kwargs):
        self.calcular_impuestos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Factura {self.id} - {self.cliente}"

    # def save(self, *args, **kwargs):
    #     self.calcular_iva_y_total()
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"Factura {self.id} - {self.cliente}"
    
class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualizar subtotal de la factura
        factura = self.factura
        factura.subtotal = sum(det.subtotal for det in factura.detalles.all())
        factura.save(update_fields=[
            'subtotal', 'iva_valor', 'imp_consumo_valor', 
            'retefuente_valor', 'total_con_impuestos'
        ])    

class Empresa(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=200, default="EMPRESA XYZ LTDA")
    nit = models.CharField(max_length=20, default="901.234.567-8")
    direccion = models.TextField(default="Calle 123 #45-67, Bogotá, Colombia")
    telefono = models.CharField(max_length=20, default="+57 300 123 4567")
    email = models.EmailField(default="facturacion@empresa.com")
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    
    def __str__(self):
        return self.nombre



# class DetalleFactura(models.Model):
#     factura = models.ForeignKey(Factura, related_name='detalles', on_delete=models.CASCADE)
#     producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
#     cantidad = models.PositiveIntegerField(default=1)
#     precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
#     subtotal = models.DecimalField(max_digits=12, decimal_places=2)

#     def save(self, *args, **kwargs):
#         self.subtotal = self.cantidad * self.precio_unitario
#         super().save(*args, **kwargs)
#         # Recalcular total de la factura
#         factura = self.factura
#         factura.total = sum(det.subtotal for det in factura.detalles.all())
#         factura.save(update_fields=['total', 'iva', 'total_con_iva'])  # ¡Importante!