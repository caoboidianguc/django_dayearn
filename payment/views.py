from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
import stripe, os
from ledger.models import Service, Price
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from ledger.views import contactEmail
from django.utils import timezone

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


# https://docs.stripe.com/checkout/fulfillment?lang=python
def fulfill_checkout(session):
    session_data = stripe.checkout.Session.retrieve(session['id'], expand=['line_items'])
    client_email = session_data['customer_details']['email']
    client_name = session_data['customer_details']['name']
    line_items = session_data['line_items']['data']
    total = session_data['amount_total'] / 100  # Convert cents to dollars
    currency = session_data['currency']
    services = []
    for item in line_items:
        description = item['description']
        total_amount = item['amount_total'] / 100
        services.append({
            'description': description,
            'total_price': total_amount,
        })


    payment_time_local = timezone.localtime(timezone.now())
    payment_time_str = payment_time_local.strftime("%B %d, %Y, at %I:%M %p %Z")
    context = {
        'client_email': client_email,
        'client_name': client_name,
        'services': services,
        'total_amount': total,
        'currency': currency,
        'payment_time': payment_time_str,
    }
    body = render_to_string('payment/confirmation_email.html', context)
    email = EmailMessage(
        subject='Payment Confirmation',
        body=body,
        from_email=contactEmail,
        to=[client_email],
    )
    email.content_subtype = 'html'
    email.send()

# stripe listen --forward-to localhost:8000/payment/webhooks/stripe/
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('endpoint_secret')
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if (event['type'] == 'checkout.session.completed'
        or event['type'] == 'checkout.session.async_payment_succeeded'):
        session = event['data']['object']
        fulfill_checkout(session)
    return HttpResponse(status=200)

