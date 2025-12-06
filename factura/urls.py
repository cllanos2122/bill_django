from django.urls import path
from . import views

app_name = 'factura'

urlpatterns = [
    
    path('', views.factura_list, name='factura_list'),
    path('crear/', views.crear_factura, name='crear_factura'),
    path('pdf/<int:factura_id>/', views.ver_factura_pdf, name='ver_factura_pdf'),
    path('xml/<int:factura_id>/', views.descargar_factura_xml, name='descargar_factura_xml'),
    path('factura/editar/<int:factura_id>/', views.editar_factura, name='editar_factura'),
    path('configurar-empresa/', views.configurar_empresa, name='configurar_empresa'),
    
    # Nuevas rutas para el menú
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('productos/', views.producto_list, name='producto_list'),
    path('reportes/', views.reporte_ventas, name='reporte_ventas'),
    
    
    # Clientes
    #path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
   
   # Productos
    #path('productos/', views.producto_list, name='producto_list'),
    path('productos/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    
    
    
    
    
]