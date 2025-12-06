from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

class FacturaListView(LoginRequiredMixin, ListView):
    model = Factura
    template_name = 'facturacion/facturas.html'
    context_object_name = 'facturas'

    def get_queryset(self):
        return Factura.objects.filter(creado_por=self.request.user)