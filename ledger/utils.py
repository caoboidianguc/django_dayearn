from .models import KhachVisit
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

contactEmail = 'Elegant Nail Spa <info@elegantnail.net>'
privacyEmail = "info@elegantnail.net"
tenSpa = "Elegant Nails & Spa"
chuDe = "Elegant Nails & Spa Confirm schedule"
address = "4605 Forest Dr #5, Columbia, SC 29206"

def saveKhachVisit(client, date, time, services, tech, status):
    try:
        khachvisit = KhachVisit(client=client, day_comes=date, time_at=time,technician=tech, status=status)
        khachvisit.save()
        khachvisit.services.set(services)
        khachvisit.total_spent = sum(dv.price for dv in services)
        khachvisit.save(update_fields=['total_spent'])
    except ValueError as e:
        print(f"Error saving KhachVisit: {e}")
        return

def cancelKhachVisit(client):
    try:
        visit = KhachVisit.objects.filter(client=client)
        for item in visit:
            item.delete()
    except ValueError as e:
        print(f"Error retrived visit: {e}")
        return

def sendEmailConfirmation(request, client):
    if not client.email:
        return
    
    email_body = {
                'client': client,
            }
    html_content = render_to_string('datHen/email_confirm_dathen.html', email_body)
    text_content = render_to_string('datHen/email_confirm_dathen.txt', email_body)

    email = EmailMultiAlternatives(
        subject='Appointment Confirmation at Elegant Nails & Spa',
        body=text_content,
        from_email=contactEmail,
        to=[client.email],
        reply_to=[privacyEmail],
    )
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return
    
    
    
def sendEmailCanceled(client):
    if not client.email:
        return
    email_body = {
                'client': client,
            }
    html_content = render_to_string('datHen/email_confirm_cancel.html', email_body)
    text_content = render_to_string('datHen/email_confirm_cancel.txt', email_body)
    email = EmailMultiAlternatives(
        subject='Appointment Cancellation',
        body=text_content,
        from_email=contactEmail,
        to=[client.email],
        reply_to=[privacyEmail],
    )
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
    except Exception as e:
        print(f"Error sending cancellation email: {e}")
        return
    # print("Email sent to client:", client.email)

def cancel_visit(request, id):
    url = reverse_lazy('datHen:cancel_confirm', kwargs={'pk': id})
    link = request.build_absolute_uri(url)
    return link

def visit_isPaid(request, pk):
    visit = get_object_or_404(KhachVisit, id=pk)
    if visit.isPaid:
        return JsonResponse({'success': True, 'isPaid': True})
    return JsonResponse({'isPaid': False})