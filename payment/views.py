from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
import stripe, os
from ledger.models import Service, Price
from django.shortcuts import render, redirect

stripe.api_key = os.environ.get('stripe_secret_key')

class ServicesPaymentView(TemplateView):
    template_name = 'payment/services_payment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = Service.objects.all
        return context
    
class SuccessCheckoutView(TemplateView):
    template_name = 'payment/success_checkout.html'
    
class CancelCheckoutView(TemplateView):
    template_name = 'payment/cancel_checkout.html'
    
class CreateCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        service = Service.objects.get(id=self.kwargs['pk'])
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product': service.stripe_product_id,
                            'unit_amount': int(service.price * 100),  # Convert to cents
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri(reverse_lazy('payment:success_checkout')),
                cancel_url=request.build_absolute_uri(reverse_lazy('payment:cancel_checkout')),
            )
            return redirect(session.url, code=303)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
class CreateMultipleCheckoutSessionView(View):
    def post(self, request, *args, **kwargs):
        service_ids = request.POST.getlist('service_ids')
        services = Service.objects.filter(id__in=service_ids)
        
        try:
            line_items = []
            for service in services:
                if not service.stripe_product_id:
                    return JsonResponse({'error': 'Service does not have a Stripe product ID'}, status=400)
                
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product': service.stripe_product_id,
                        'unit_amount': int(service.price * 100),  # Convert to cents
                    },
                    'quantity': 1,
                })
                
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse_lazy('payment:success_checkout')),
                cancel_url=request.build_absolute_uri(reverse_lazy('payment:cancel_checkout')),
            )
            return redirect(session.url, code=303)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)