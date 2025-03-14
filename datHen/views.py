from typing import Any
from django.shortcuts import render, redirect, get_object_or_404
from ledger.models import Khach, Technician, Service
from django.views.generic import View
from django.views.generic.edit import UpdateView, CreateView
from django.urls import reverse_lazy
from .forms import (UserExistClientForm, ExistClientForm, DateForm, ThirdForm, 
                    ThirdFormExist, ServicesChoiceForm, KhachDetailForm)
from datetime import timedelta, date, datetime
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

chuDe = "Elegant Nails & Spa Confirm schedule"
tenSpa = "Elegant Nails & Spa"
cancleAppointment = "https://quangvu.pythonanywhere.com/dathen/get_client/"

class DatHenView(LoginRequiredMixin,View):
    template_name = 'datHen/dathenview.html'
    def get(self, request):
        date_str = request.GET.get('date')
        if date_str:
            try:
                selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = timezone.now().date()
        else:
            selected_date = timezone.now().date()
        prev_day = selected_date - timedelta(days=1)
        next_day = selected_date + timedelta(days=1)
        all_tech = Technician.objects.filter(owner=request.user)
        context = {
            'allTech' : all_tech,
            'selected_date': selected_date,
            'prev_day' : prev_day,
            'next_day' : next_day,
        }
        for tech in all_tech:
            tech.clients = tech.get_clients().filter(day_comes=selected_date).order_by('time_at')
        return render(request, self.template_name, context)


class UserFindClient(LoginRequiredMixin,View):
    template = 'datHen/exist_client_user.html'
    def get(self, request):
        phone = request.GET.get('phone')
        form = UserExistClientForm()
        khach = Khach.objects.filter(phone=phone)
        cont = {'formDatHen': form, 'khach': khach}
        return render(request, self.template, cont)
    
class FindClient(View):
    template = 'datHen/exist_client_hen_cancel.html'
    def get(self, request):
        name = str(request.GET.get("full_name")).upper().strip()
        phone = request.GET.get('phone')
        form = ExistClientForm()
        khach = Khach.objects.filter(full_name=name, phone=phone)
        cont = {'formDatHen': form, 'khach': khach}
        return render(request, self.template, cont)
    
class ExistFound(View):
    template = 'datHen/exist_pick_tech.html'
    
    def get(self, request, pk):
        request.session['client_id'] = ""
        tech = Technician.objects.all()
        cont = {'allTech': tech}
        request.session['client_id'] = pk
        return render(request, self.template, cont)
    
class ExistSecond(View):
    template = 'datHen/exist_second.html'
    def get(self, request, pk):
        # request.session['tech_id'] = ""
        request.session['date'] = request.GET.get('day_comes')
        # date = request.session['date']
        tech = get_object_or_404(Technician, id=pk)        
        secondForm = DateForm()
        cont = {
                'secondForm': secondForm,
            }
        request.session['tech_id'] = pk
        return render(request, self.template, cont)

class ChoiceServicesExistView(View):
    template = 'datHen/services_choice_exist.html'

    def get(self, request):
        serviceForm = ServicesChoiceForm(request.GET)
        request.session['date'] = request.GET.get('day_comes')
        cont = {
            'form': serviceForm
        }
        return render(request, self.template, cont)
    
    
class ExistThirdStep(View):
    template = 'datHen/exist_third_step.html'
    gioHienTai = datetime.now() + timedelta(hours=1)
    hnay = date.today().strftime("%Y-%m-%d")
    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy('datHen:listHen')
        return reverse_lazy('ledger:index')
    def get(self,request):
        client_id = request.session['client_id']
        pk = request.session['tech_id']
        tech = get_object_or_404(Technician, id=pk)
        client = get_object_or_404(Khach, id=client_id)
        ngay = request.session['date']
        
        serChon = request.GET.getlist('dichvu')
        request.session['dichvu'] = [int(service) for service in serChon]
        services = Service.objects.filter(id__in=[int(service) for service in serChon])
        time_perform = sum([service.time_perform.total_seconds() for service in services]) / 60
        available = []
        ngayDate = datetime.strptime(ngay, "%Y-%m-%d").date()
        if ngay == self.hnay:
            available = tech.get_available_with(ngay=ngay, thoigian=time_perform)
            available = [gio for gio in available if gio.hour > self.gioHienTai.hour]
        elif ngayDate.weekday() == 6 or tech.is_on_vacation(check_date=ngayDate):
            available = []
        else:
            available = tech.get_available_with(ngay=ngay, thoigian=time_perform)
        form = ThirdFormExist(instance=client)
        form.instance.day_comes = ngay
        form.instance.technician = tech
        cont = {'form' : form, 
                'tech': tech,
                'available': available,
                'ngay': ngayDate}
        
        return render(request, self.template, cont)
    
    def post(self,request):
        client_id = request.session['client_id']
        pk = request.session['tech_id']
        tech = get_object_or_404(Technician, id=pk)
        client = get_object_or_404(Khach, id=client_id)
        ngay = request.session['date']
        serChon = request.GET.getlist('dichvu')
        request.session['dichvu'] = [int(service) for service in serChon]
        services = Service.objects.filter(id__in=[int(service) for service in serChon])
        available = []
        ngayDate = datetime.strptime(ngay, "%Y-%m-%d").date()
        time_perform = sum([service.time_perform.total_seconds() for service in services]) / 60
        total_point = sum([service.price for service in services])
        if ngayDate.weekday() == 6 or tech.is_on_vacation(ngayDate):
            available = []
        else:
            available = tech.get_available_with(ngay=ngay, thoigian=time_perform)
        form = ThirdFormExist(request.POST, instance=client)
        if not form.is_valid():
            cont = {'form' : form, 
                'tech': tech,
                'available': available,
                'ngay': ngayDate}
            return render(request, self.template, cont)
        
        khac = form.save(commit=False)
        khac.day_comes = ngay
        khac.technician = tech
        khac.points = total_point
        khac.save()
        khac.services.set(services)
        form.save_m2m()
        tinNhan = f"Thank you for booking with {tenSpa}! \nYour appointment is set for: \nDate: {form.instance.day_comes} \nTime: {form.instance.time_at} \nTechnician: {form.instance.technician} \nNeed to change anything? Just give us a call!"
        messages.success(request, f"{form.instance.full_name} was scheduled successfully!")
        EmailMessage(chuDe, tinNhan, to=[form.instance.email]).send()
        thongbao = f"{form.instance.full_name} booked appointment with you on {form.instance.day_comes} at {form.instance.time_at}"
        if tech.email != None:
            EmailMessage(chuDe, thongbao, to=[tech.email]).send()
                    
        return redirect(self.get_success_url())

class FirstStep(View):
    template = 'datHen/first_step.html'
    tech = Technician.objects.all()
    def get(self,request):
        cont = {'tech': self.tech}
        return render(request, self.template, cont)


class Second(View):
    template = 'datHen/second.html'
    def get(self, request, pk):
        request.session['id'] = None
        request.session['date'] = request.GET.get('day_comes')      
        secondForm = DateForm()
        cont = {
                'secondForm': secondForm,
            }
        request.session['id'] = pk
        return render(request, self.template, cont)


class ChoiceServicesView(View):
    template = 'datHen/services_choice.html'

    def get(self, request):
        serviceForm = ServicesChoiceForm(request.GET)
        request.session['date'] = request.GET.get('day_comes')
        cont = {
            'form': serviceForm
        }
        return render(request, self.template, cont)
    

class ThirdStep(View):
    template = 'datHen/third_step.html'
    gioHienTai = datetime.now() + timedelta(hours=1)
    hnay = date.today().strftime("%Y-%m-%d")
    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy('datHen:listHen')
        return reverse_lazy('ledger:index')
    def get(self,request):
        pk = request.session['id']
        tech = get_object_or_404(Technician, id=pk)
        ngay = request.session['date']
        
        serChon = request.GET.getlist('dichvu')
        request.session['dichvu'] = [int(service) for service in serChon]
        services = Service.objects.filter(id__in=[int(service) for service in serChon])
        
        time_perform = sum([service.time_perform.total_seconds() for service in services]) / 60
        available = []
        ngayDate = datetime.strptime(ngay, "%Y-%m-%d").date()
        if ngay == self.hnay:
            available = tech.get_available_with(ngay=ngay, thoigian=time_perform)
            available = [gio for gio in available if gio.hour >= self.gioHienTai.hour]
        elif ngayDate.weekday() == 6 or tech.is_on_vacation(ngayDate):
            available = []
        else:
            available = tech.get_available_with(ngay=ngay, thoigian=time_perform)
        form = ThirdForm()
        form.instance.day_comes = ngay
        cont = {'form' : form, 
                'tech': tech,
                'available': available,
                'ngay': ngayDate,
                'allServices': services
                }
        form.instance.technician = tech
        return render(request, self.template, cont)
    
    def post(self,request):
        pk = request.session['id']
        tech = get_object_or_404(Technician, id=pk)
        ngay = request.session['date']
        serChon = request.GET.getlist('dichvu')
        request.session['dichvu'] = [int(service) for service in serChon]
        services = Service.objects.filter(id__in=[int(service) for service in serChon])
        available = []
        time_perform = sum([service.time_perform.total_seconds() for service in services]) / 60
        total_point = sum([service.price for service in services])
        ngayDate = datetime.strptime(ngay, "%Y-%m-%d").date()
        if ngayDate.weekday() == 6 or tech.is_on_vacation(ngayDate):
            available = []
        else:
            available = tech.get_available_with(ngay=ngay, thoigian=time_perform)
            
        form = ThirdForm(request.POST)
        
        if not form.is_valid():
            cont = {'form' : form, 
                'tech': tech,
                'available': available,
                'ngay': ngayDate,
                'allServices': services}
            return render(request, self.template, cont)
        
        khac = form.save(commit=False)
        khac.day_comes = ngay
        khac.technician = tech
        khac.points = total_point
        khac.save()
        khac.services.set(services)
        form.save_m2m()
        tinNhan = f"Thank you for booking with {tenSpa}! \nYour appointment is set for: \nDate: {form.instance.day_comes} \nTime: {form.instance.time_at} \nTechnician: {form.instance.technician} \nNeed to change anything? Just give us a call!"
        messages.success(request, f"{form.instance.full_name} was scheduled successfully!")
        EmailMessage(chuDe, tinNhan, to=[form.instance.email]).send()
        thongbao = f"{form.instance.full_name} booked appointment with you on {form.instance.day_comes} at {form.instance.time_at}"
        if tech.email != None:
            EmailMessage(chuDe, thongbao, to=[tech.email]).send()
                    
        return redirect(self.get_success_url())
    

class CancelViewConfirm(View):
    template = "datHen/confirm_cancel.html"
    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy('datHen:listHen')
        return reverse_lazy('ledger:index')
    def get(self, request, pk):
        client = get_object_or_404(Khach, id=pk)
        context = {
            'client': client
        }
        return render(request, self.template, context)
    
    def post(self, request, pk):
        client = get_object_or_404(Khach, id=pk)
        
        total_point = sum([service.price for service in client.services.all()])
        client.points -= total_point
        client.services.clear()
        client.status = Khach.Status.cancel
        client.save()
        messages.success(request, "Your services have been successfully canceled.")
        return redirect(self.get_success_url())
    

class ClientDetailView(LoginRequiredMixin, UpdateView):
    template_name = 'datHen/client_detail.html'
    form_class = KhachDetailForm
    success_url = reverse_lazy('datHen:listHen')
    def get_object(self, queryset = None):
        pk=self.kwargs.get('pk')
        return get_object_or_404(Khach, id=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_object()
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        services = form.cleaned_data['services']
        totalPoint = sum(dv.price for dv in services)
        self.object.points = totalPoint
        self.object.save()
        form.save_m2m()
        return super().form_valid(form)

    def get_success_url(self):
        return self.success_url

