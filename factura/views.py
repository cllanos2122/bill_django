#from django.shortcuts import render

# Create your views here.

# Desarrollo de cllanos 2025 - huellitas
# =============================================================================
# 
# from django.db.models import Sum
# from django.utils import timezone
# from datetime import timedelta
# 
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.views.generic import ListView
# 
# from django.contrib.auth.models import User
# from django.core.validators import MinValueValidator
# 
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.http import HttpResponse
# from .models import Factura, Cliente, Producto, DetalleFactura
# from .forms import FacturaForm, DetalleFacturaForm
# from .utils import render_pdf_factura
# 
# =============================================================================


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
# class FacturaListView(LoginRequiredMixin, ListView):
#     model = Factura
#     template_name = 'facturacion/facturas.html'
#     context_object_name = 'facturas'
# 
#     def get_queryset(self):
#         return Factura.objects.filter(creado_por=self.request.user)
#     
#     # views.py
# 
# 
# class ReporteVentasView(LoginRequiredMixin, TemplateView):
#     template_name = 'facturacion/reportes.html'
# 
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         hoy = timezone.now().date()
#         semana_pasada = hoy - timedelta(days=7)
# 
#         ventas_semana = Factura.objects.filter(
#             creado_por=self.request.user,
#             fecha__date__gte=semana_pasada,
#             estado='pagada'
#         ).aggregate(total=Sum('total'))['total'] or 0
# 
#         context['ventas_semana'] = ventas_semana
#         return context
#     
# 
##from .forms import FacturaForm,  
# =============================================================================

import io
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from decimal import Decimal, InvalidOperation 
from .models import Factura, Cliente, Producto, DetalleFactura, Empresa
from factura.utils import render_pdf_factura
from .forms import ClienteForm, ProductoForm, FacturaImpuestosForm, EmpresaForm
from .xml_generator import generar_factura_xml


# @login_required
# def factura_list(request):
#     facturas = Factura.objects.filter(creado_por=request.user).order_by('-fecha')
@login_required
def factura_list(request):
    # Asegúrate de que solo obtienes facturas con ID válido
    facturas = Factura.objects.filter(
        creado_por=request.user
    ).exclude(id__isnull=True).order_by('-fecha')
    return render(request, 'facturacion/factura_list.html', {'facturas': facturas})

# @login_required
# def crear_factura(request):
#     if request.method == 'POST':
#         factura_form = FacturaForm(request.POST, user=request.user)
#         if factura_form.is_valid():
#             factura = factura_form.save(commit=False)
#             factura.creado_por = request.user
#             factura.total = 0
#             factura.save()  # Esto inicializa IVA y total_con_iva

#             productos_ids = request.POST.getlist('producto_id')
#             cantidades = request.POST.getlist('cantidad')

#             for prod_id, cant in zip(productos_ids, cantidades):
#                 try:
#                     producto = Producto.objects.get(id=prod_id, creado_por=request.user)
#                     cantidad = int(cant)
#                     if cantidad < 1:
#                         raise ValueError("Cantidad debe ser >= 1")
#                     subtotal = producto.precio * cantidad
#                     DetalleFactura.objects.create(
#                         factura=factura,
#                         producto=producto,
#                         cantidad=cantidad,
#                         precio_unitario=producto.precio,
#                         subtotal=subtotal
#                     )
#                 except (Producto.DoesNotExist, ValueError, TypeError):
#                     messages.error(request, "Error en los datos del producto.")
#                     factura.delete()
#                     return redirect('crear_factura')

#             # Recalcular totales (ya se hace en DetalleFactura.save)

#             # Enviar email si se pidió y el cliente tiene email
#             enviar_email = factura_form.cleaned_data.get('enviar_email')
#             if enviar_email and factura.cliente.email:
#                 buffer = io.BytesIO()
#                 render_pdf_factura(buffer, factura)
#                 email = EmailMessage(
#                     subject=f"Tu factura #{factura.id}",
#                     body=f"Hola {factura.cliente.nombre},\n\nAdjuntamos tu factura. ¡Gracias por tu compra!",
#                     from_email=settings.DEFAULT_FROM_EMAIL,
#                     to=[factura.cliente.email],
#                 )
#                 email.attach(f'factura_{factura.id}.pdf', buffer.getvalue(), 'application/pdf')
#                 try:
#                     email.send()
#                     messages.success(request, "Factura creada y enviada por email.")
#                 except Exception as e:
#                     messages.warning(request, f"Factura creada, pero no se pudo enviar el email: {e}")
#             else:
#                 messages.success(request, "Factura creada exitosamente.")

#             return redirect('factura_list')
#     else:
#         factura_form = FacturaForm(user=request.user)

#     productos = Producto.objects.filter(creado_por=request.user)
#     clientes = Cliente.objects.filter(creado_por=request.user)
#     return render(request, 'facturacion/factura_form.html', {
#         'factura_form': factura_form,
#         'productos': productos,
#         'clientes': clientes
#     })

# @login_required
# def crear_factura(request):
#     if request.method == 'POST':
#         # 1. Manejar cliente
#         cliente_id = request.POST.get('cliente')
#         if cliente_id:
#             cliente = get_object_or_404(Cliente, id=cliente_id, creado_por=request.user)
#         else:
#             # Crear nuevo cliente
#             cliente = Cliente.objects.create(
#                 nombre=request.POST.get('nuevo_cliente_nombre', '').strip(),
#                 email=request.POST.get('nuevo_cliente_email', '').strip(),
#                 telefono=request.POST.get('nuevo_cliente_telefono', '').strip(),
#                 direccion=request.POST.get('nuevo_cliente_direccion', '').strip(),
#                 creado_por=request.user
#             )

#         # 2. Crear factura
#         factura = Factura.objects.create(
#             cliente=cliente,
#             estado='pendiente',
#             creado_por=request.user
#         )

#         # 3. Manejar productos
#         producto_ids = request.POST.getlist('producto_id_hidden')
#         cantidades = request.POST.getlist('cantidad')
#         nuevos_nombres = request.POST.getlist('nuevo_producto_nombre')
#         nuevos_precios = request.POST.getlist('nuevo_producto_precio')

#         # Alinear listas
#         for i in range(len(cantidades)):
#             cantidad = int(cantidades[i]) if cantidades[i] else 0
#             if cantidad <= 0:
#                 continue

#             if i < len(producto_ids) and producto_ids[i]:
                
#                 # Producto existente
#                 producto = get_object_or_404(Producto, id=producto_ids[i], creado_por=request.user)
#                 precio = producto.precio
#             elif i < len(nuevos_nombres) and nuevos_nombres[i].strip():
#                 # Nuevo producto
#                 precio = Decimal(nuevos_precios[i]) if nuevos_precios[i] else Decimal('0.00')
#                 producto = Producto.objects.create(
#                     nombre=nuevos_nombres[i].strip(),
#                     precio=precio,
#                     creado_por=request.user
#                 )
#             else:
#                 continue

#             DetalleFactura.objects.create(
#                 factura=factura,
#                 producto=producto,
#                 cantidad=cantidad,
#                 precio_unitario=producto.precio,
#                 subtotal=producto.precio * cantidad
#             )

#         # 4. Enviar email si se pide
#         if request.POST.get('enviar_email') and cliente.email:
#             buffer = io.BytesIO()
#             render_pdf_factura(buffer, factura)
#             email = EmailMessage(
#                 subject=f"Tu factura #{factura.id}",
#                 body=f"Hola {cliente.nombre},\n\nAdjuntamos tu factura. ¡Gracias por tu compra!",
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[cliente.email],
#             )
#             email.attach(f'factura_{factura.id}.pdf', buffer.getvalue(), 'application/pdf')
#             try:
#                 email.send()
#                 messages.success(request, "Factura creada y enviada por email.")
#             except Exception as e:
#                 messages.warning(request, f"Factura creada, pero no se pudo enviar el email: {e}")
#         else:
#             messages.success(request, "Factura creada exitosamente.")

#         return redirect('facturacion:factura_list')

#     else:
#         clientes = Cliente.objects.filter(creado_por=request.user)
#         productos = Producto.objects.filter(creado_por=request.user)
#         return render(request, 'facturacion/factura_form.html', {
#             'clientes': clientes,
#             'productos': productos
#         })


# @login_required
# def crear_factura(request):
#     if request.method == 'POST':
#         # --- Manejo de cliente (igual que antes) ---
#         cliente_id = request.POST.get('cliente')
#         if cliente_id:
#             cliente = get_object_or_404(Cliente, id=cliente_id, creado_por=request.user)
#         else:
#             cliente = Cliente.objects.create(
#                 nombre=request.POST.get('nuevo_cliente_nombre', '').strip(),
#                 email=request.POST.get('nuevo_cliente_email', '').strip(),
#                 telefono=request.POST.get('nuevo_cliente_telefono', '').strip(),
#                 direccion=request.POST.get('nuevo_cliente_direccion', '').strip(),
#                 creado_por=request.user
#             )

#         # --- Crear factura ---
#         factura = Factura.objects.create(
#             cliente=cliente,
#             estado='pendiente',
#             creado_por=request.user
#         )

#         # --- Manejo de productos ---
#         producto_ids = request.POST.getlist('producto_id_hidden')
#         cantidades = request.POST.getlist('cantidad')
#         nuevos_nombres = request.POST.getlist('nuevo_producto_nombre')
#         nuevos_precios = request.POST.getlist('nuevo_producto_precio')

#         for i in range(len(cantidades)):
#             try:
#                 cantidad = int(cantidades[i])
#                 if cantidad <= 0:
#                     continue
#             except (ValueError, TypeError):
#                 continue

#             # Producto existente
#             if i < len(producto_ids) and producto_ids[i]:
#                 try:
#                     producto = Producto.objects.get(id=producto_ids[i], creado_por=request.user)
#                     precio_unitario = producto.precio  # Ya es Decimal
#                 except Producto.DoesNotExist:
#                     messages.error(request, "Producto no encontrado.")
#                     continue

#             # Nuevo producto
#             elif i < len(nuevos_nombres) and nuevos_nombres[i].strip():
#                 nombre_producto = nuevos_nombres[i].strip()
#                 precio_str = nuevos_precios[i].strip() if i < len(nuevos_precios) else '0'
                
#                 # ✅ Conversión SEGURA de string a Decimal
#                 try:
#                     if precio_str:
#                         # Elimina espacios y valida
#                         precio_unitario = Decimal(request.POST['precio'].replace(',', '.'))
#                     else:
#                         precio_unitario = Decimal('0.00')
#                 except (InvalidOperation, ValueError):
#                     messages.error(request, f"Precio inválido para '{nombre_producto}': {precio_str}")
#                     continue

#                 # Crear nuevo producto
#                 producto = Producto.objects.create(
#                     nombre=nombre_producto,
#                     precio=precio_unitario,  # ← Decimal, no float
#                     creado_por=request.user
#                 )

#             else:
#                 continue

#             # ✅ Ahora la multiplicación es Decimal * int → Decimal (¡válido!)
#             subtotal = precio_unitario * cantidad

#             DetalleFactura.objects.create(
#                 factura=factura,
#                 producto=producto,
#                 cantidad=cantidad,
#                 precio_unitario=precio_unitario,
#                 subtotal=subtotal  # ← Decimal
#             )
@login_required
def crear_factura(request):
    if request.method == 'POST':
        # Manejar cliente (igual que antes)
        cliente_id = request.POST.get('cliente')
        if cliente_id:
            cliente = get_object_or_404(Cliente, id=cliente_id, creado_por=request.user)
        else:
            cliente = Cliente.objects.create(
                nombre=request.POST.get('nuevo_cliente_nombre', '').strip(),
                documento_identidad=request.POST.get('nuevo_cliente_documento', '').strip(),  # ← Nuevo campo
                email=request.POST.get('nuevo_cliente_email', '').strip(),
                telefono=request.POST.get('nuevo_cliente_telefono', '').strip(),
                direccion=request.POST.get('nuevo_cliente_direccion', '').strip(),
                creado_por=request.user
            )

        # Crear factura con impuestos
        factura = Factura.objects.create(
            cliente=cliente,
            estado=request.POST.get('estado', 'pendiente'),
            iva_porcentaje=Decimal(request.POST.get('iva_porcentaje', '21.00')),
            imp_consumo_porcentaje=Decimal(request.POST.get('imp_consumo_porcentaje', '0.00')),
            retefuente_porcentaje=Decimal(request.POST.get('retefuente_porcentaje', '0.00')),
            creado_por=request.user
        )

        # Manejar productos (igual que antes, pero sin calcular subtotal aquí)
        producto_ids = request.POST.getlist('producto_id_hidden')
        cantidades = request.POST.getlist('cantidad')
        nuevos_nombres = request.POST.getlist('nuevo_producto_nombre')
        nuevos_precios = request.POST.getlist('nuevo_producto_precio')

        for i in range(len(cantidades)):
            try:
                cantidad = int(cantidades[i])
                if cantidad <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            if i < len(producto_ids) and producto_ids[i]:
                try:
                    producto = Producto.objects.get(id=producto_ids[i], creado_por=request.user)
                    precio_unitario = producto.precio
                except Producto.DoesNotExist:
                    continue
            elif i < len(nuevos_nombres) and nuevos_nombres[i].strip():
                nombre_producto = nuevos_nombres[i].strip()
                precio_str = nuevos_precios[i].strip() if i < len(nuevos_precios) else '0'
                try:
                    precio_unitario = Decimal(precio_str.replace(',', '.'))
                except (InvalidOperation, ValueError):
                    continue
                producto = Producto.objects.create(
                    nombre=nombre_producto,
                    precio=precio_unitario,
                    creado_por=request.user
                )
            else:
                continue

            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=precio_unitario * cantidad
            )

        # El subtotal y total se calculan automáticamente en DetalleFactura.save()
        # --- Envío de email (igual que antes) ---
        if request.POST.get('enviar_email') and cliente.email:
            buffer = io.BytesIO()
            render_pdf_factura(buffer, factura)
            email = EmailMessage(
                subject=f"Tu factura #{factura.id}",
                body=f"Hola {cliente.nombre},\n\nAdjuntamos tu factura. ¡Gracias por tu compra!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[cliente.email],
            )
            email.attach(f'factura_{factura.id}.pdf', buffer.getvalue(), 'application/pdf')
            try:
                email.send()
                messages.success(request, "Factura creada y enviada por email.")
            except Exception as e:
                messages.warning(request, f"Factura creada, pero no se pudo enviar el email: {e}")
        else:
            messages.success(request, "Factura creada exitosamente.")

        return redirect('factura:factura_list')

    else:
        clientes = Cliente.objects.filter(creado_por=request.user)
        productos = Producto.objects.filter(creado_por=request.user)
        
        return render(request, 'facturacion/factura_form.html', {
            'clientes': clientes,
            'productos': productos,
            
        })



@login_required
def ver_factura_pdf(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id, creado_por=request.user)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{factura.id}.pdf"'
    render_pdf_factura(response, factura)
    return response

@login_required
def cliente_list(request):
    clientes = Cliente.objects.filter(creado_por=request.user)
    return render(request, 'facturacion/cliente_list.html', {'clientes': clientes})

@login_required
def producto_list(request):
    productos = Producto.objects.filter(creado_por=request.user)
    return render(request, 'facturacion/producto_list.html', {'productos': productos})

# @login_required
# def reporte_ventas(request):
#     facturas = Factura.objects.filter(
#         creado_por=request.user,
#         estado='pagada'
#     ).order_by('-fecha')
    
#     total_ventas = facturas.aggregate(total=Sum('total_con_iva'))['total'] or 0
    
#     return render(request, 'facturacion/reporte_ventas.html', {
#         'facturas': facturas,
#         'total_ventas': total_ventas
#     })

@login_required
def reporte_ventas(request):
    # Mostrar TODAS las facturas (no solo pagadas)
    facturas = Factura.objects.filter(
        creado_por=request.user
    ).order_by('-fecha')
    
    total_ventas = facturas.aggregate(
        total=Sum('total_con_impuestos')
    )['total'] or 0
    
    return render(request, 'facturacion/reporte_ventas.html', {
        'facturas': facturas,
        'total_ventas': total_ventas
    })


@login_required
def cliente_list(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.creado_por = request.user
            cliente.save()
            messages.success(request, f"Cliente '{cliente.nombre}' creado exitosamente.")
            return redirect('factura:cliente_list')
    else:
        form = ClienteForm()
    
    clientes = Cliente.objects.filter(creado_por=request.user)
    return render(request, 'facturacion/cliente_list.html', {
        'clientes': clientes,
        'form': form
    })

@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id, creado_por=request.user)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cliente '{cliente.nombre}' actualizado exitosamente.")
            return redirect('factura:cliente_list')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'facturacion/cliente_form.html', {'form': form, 'cliente': cliente})

@login_required
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id, creado_por=request.user)
    nombre = cliente.nombre
    cliente.delete()
    messages.success(request, f"Cliente '{nombre}' eliminado exitosamente.")
    return redirect('factura:cliente_list')

@login_required
def producto_list(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.creado_por = request.user
            producto.save()
            messages.success(request, f"Producto '{producto.nombre}' creado exitosamente.")
            return redirect('factura:producto_list')
    else:
        form = ProductoForm()
    
    productos = Producto.objects.filter(creado_por=request.user)
    return render(request, 'facturacion/producto_list.html', {
        'productos': productos,
        'form': form
    })

@login_required
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, creado_por=request.user)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Producto '{producto.nombre}' actualizado exitosamente.")
            return redirect('factura:producto_list')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'facturacion/producto_form.html', {'form': form, 'producto': producto})

@login_required
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, creado_por=request.user)
    nombre = producto.nombre
    producto.delete()
    messages.success(request, f"Producto '{nombre}' eliminado exitosamente.")
    return redirect('factura:producto_list')



@login_required
def editar_factura(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id, creado_por=request.user)
    
    if request.method == 'POST':
        # Actualizar impuestos
        factura.estado = request.POST.get('estado', factura.estado)
        factura.iva_porcentaje = Decimal(request.POST.get('iva_porcentaje', factura.iva_porcentaje))
        factura.imp_consumo_porcentaje = Decimal(request.POST.get('imp_consumo_porcentaje', factura.imp_consumo_porcentaje))
        factura.retefuente_porcentaje = Decimal(request.POST.get('retefuente_porcentaje', factura.retefuente_porcentaje))
        factura.save()
        
        # Actualizar cliente si es necesario
        cliente_id = request.POST.get('cliente')
        if cliente_id:
            cliente = get_object_or_404(Cliente, id=cliente_id, creado_por=request.user)
            cliente.documento_identidad = request.POST.get('documento_identidad', cliente.documento_identidad)
            cliente.save()
            factura.cliente = cliente
            factura.save()
        
        # Manejar productos (simplificado: eliminamos y recreamos)
        factura.detalles.all().delete()
        
        producto_ids = request.POST.getlist('producto_id_hidden')
        cantidades = request.POST.getlist('cantidad')
        nuevos_nombres = request.POST.getlist('nuevo_producto_nombre')
        nuevos_precios = request.POST.getlist('nuevo_producto_precio')

        for i in range(len(cantidades)):
            try:
                cantidad = int(cantidades[i])
                if cantidad <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            if i < len(producto_ids) and producto_ids[i]:
                try:
                    producto = Producto.objects.get(id=producto_ids[i], creado_por=request.user)
                    precio_unitario = producto.precio
                except Producto.DoesNotExist:
                    continue
            elif i < len(nuevos_nombres) and nuevos_nombres[i].strip():
                nombre_producto = nuevos_nombres[i].strip()
                precio_str = nuevos_precios[i].strip() if i < len(nuevos_precios) else '0'
                try:
                    precio_unitario = Decimal(precio_str.replace(',', '.'))
                except (InvalidOperation, ValueError):
                    continue
                producto = Producto.objects.create(
                    nombre=nombre_producto,
                    precio=precio_unitario,
                    creado_por=request.user
                )
            else:
                continue

            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=precio_unitario * cantidad
            )

        messages.success(request, f"Factura #{factura.id} actualizada exitosamente.")
        return redirect('factura:factura_list')
    
    else:
        clientes = Cliente.objects.filter(creado_por=request.user)
        productos = Producto.objects.filter(creado_por=request.user)
        return render(request, 'facturacion/factura_edit.html', {
            'factura': factura,
            'clientes': clientes,
            'productos': productos,
        })

@login_required
def configurar_empresa(request):
    empresa, created = Empresa.objects.get_or_create(
        usuario=request.user,
        defaults={
            'nombre': 'EMPRESA XYZ LTDA',
            'nit': '901.234.567-8',
            'direccion': 'Calle 123 #45-67, Bogotá, Colombia',
            'telefono': '+57 300 123 4567',
            'email': 'facturacion@empresa.com'
        }
    )
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Información de la empresa actualizada exitosamente.")
            return redirect('factura:factura_list')
    else:
        form = EmpresaForm(instance=empresa)
    
    return render(request, 'facturacion/configurar_empresa.html', {'form': form})


@login_required
def descargar_factura_xml(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id, creado_por=request.user)
    xml_content = generar_factura_xml(factura)
    
    response = HttpResponse(xml_content, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.id}.xml"'
    return response


# =============================================================================
# @login_required
# def crear_factura(request):
#     if request.method == 'POST':
#         factura_form = FacturaForm(request.POST)
#         if factura_form.is_valid():
#             factura = factura_form.save(commit=False)
#             factura.creado_por = request.user
#             factura.total = 0
#             factura.save()
# 
#             productos_ids = request.POST.getlist('producto_id')
#             cantidades = request.POST.getlist('cantidad')
# 
#             total = 0
#             for prod_id, cant in zip(productos_ids, cantidades):
#                 try:
#                     producto = Producto.objects.get(id=prod_id, creado_por=request.user)
#                     cantidad = int(cant)
#                     if cantidad < 1:
#                         raise ValueError("Cantidad debe ser >= 1")
#                     subtotal = producto.precio * cantidad
#                     total += subtotal
#                     DetalleFactura.objects.create(
#                         factura=factura,
#                         producto=producto,
#                         cantidad=cantidad,
#                         precio_unitario=producto.precio,
#                         subtotal=subtotal
#                     )
#                 except (Producto.DoesNotExist, ValueError, TypeError):
#                     messages.error(request, "Error en los datos del producto.")
#                     factura.delete()
#                     return redirect('crear_factura')
# 
#             # El total se actualiza automáticamente vía señal en DetalleFactura.save()
#             messages.success(request, "Factura creada exitosamente.")
#             return redirect('factura_list')
#     else:
#         factura_form = FacturaForm()
#         factura_form.fields['cliente'].queryset = Cliente.objects.filter(creado_por=request.user)
# 
#     productos = Producto.objects.filter(creado_por=request.user)
#     clientes = Cliente.objects.filter(creado_por=request.user)
#     return render(request, 'facturacion_app/factura_form.html', {
#         'factura_form': factura_form,
#         'productos': productos,
#         'clientes': clientes
#     })
# 
# @login_required
# def ver_factura_pdf(request, factura_id):
#     factura = get_object_or_404(Factura, id=factura_id, creado_por=request.user)
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'inline; filename="factura_{factura.id}.pdf"'
#     render_pdf_factura(response, factura)
#     return response
# =============================================================================
