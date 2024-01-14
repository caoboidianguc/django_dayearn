from typing import Any
from django.shortcuts import render, redirect, get_object_or_404
from ledger.models import Khach, Technician
from django.views.generic import View, ListView
from django.urls import reverse_lazy
from .forms import DatHenFrom, ExistClientForm, FirstStepForm, SecondStepForm
from datetime import timedelta
from django.contrib import messages
from django.core.mail import EmailMessage
import datetime
# from django.views.generic.dates import DayArchiveView


class DatHenView(View):
    template_name = 'datHen/dathenview.html'
    def get(self, request):
        hnay = Khach.objects.filter(day_comes=datetime.datetime.today()).order_by("time_at")
        allKhachHen = {'khachHen': hnay }
        return render(request, self.template_name, allKhachHen)

# https://docs.djangoproject.com/en/5.0/ref/models/querysets/#field-lookups

    
class FindClient(View):
    template = 'datHen/exist_client_hen.html'
    success_url = reverse_lazy('datHen:listHen')
    def get(self, request):
        name = str(request.GET.get('full_name')).upper()
        khach = Khach.objects.filter(full_name=name,phone=request.GET.get('phone'))
        form = ExistClientForm()
        cont = {'formDatHen': form, 'khach': khach}
        return render(request, self.template, cont)
    
class ExistFound(View):
    template = 'datHen/layhen.html'
    success_url = reverse_lazy('datHen:listHen')
    chuDe = "Dayearns Confirm schedule"
    def get(self, request, pk):
        khach = get_object_or_404(Khach, id=pk)
        form = DatHenFrom(instance=khach)
        cont = {'formDatHen': form}
        return render(request, self.template, cont)
    
    def post(self, request, pk):
        tech = Technician.objects.all()
        khach = get_object_or_404(Khach, id=pk)
        form = DatHenFrom(request.POST, instance=khach)
        if not form.is_valid():
            cont = {'formDatHen': form}
            return render(request, self.template, cont)
        khac = form.save(commit=False)
        khac.save()
        form.save_m2m()
        if form.instance.status == "Cancel":
            tinNhan = "You had canceled. Thanks!"
        else:
            tinNhan = f"You scheduled with DayEarns \nOn: {form.instance.day_comes} \nAt: {form.instance.time_at} \nTechnician: {form.instance.technician}"
        messages.success(request, f"{form.instance.full_name} was scheduled successfully!")
        EmailMessage(self.chuDe, tinNhan, to=[form.instance.email]).send()
        thongbao = f"{form.instance.full_name} book appointment with you on {form.instance.day_comes} at {form.instance.time_at}"
        if form.instance.technician != None:
            for empl in tech:
                if form.instance.technician == empl:
                    EmailMessage(self.chuDe, thongbao, to=[empl.email]).send()
        return redirect(self.success_url)
    
    
class KhachLayHen(View):
    template = 'datHen/layhen.html'
    success_url = reverse_lazy('datHen:listHen')
    chuDe = "Dayearns Confirm schedule"
    
    def get(self, request):
        form = DatHenFrom()
        #needs more work for each Tech with time available
        cont = {'formDatHen': form}
        return render(request, self.template, cont)
    
    def post(self, request):
        tech = Technician.objects.all()
        form = DatHenFrom(request.POST)
        if not form.is_valid():
            cont = {'formDatHen': form}
            return render(request, self.template, cont)
        khac = form.save(commit=False)
        khac.save()
        form.save_m2m()
        tinNhan = f"You scheduled with DayEarns \nOn: {form.instance.day_comes} \nAt: {form.instance.time_at} \nTechnician: {form.instance.technician}"
        messages.success(request, f"{form.instance.full_name} was scheduled successfully!")
        EmailMessage(self.chuDe, tinNhan, to=[form.instance.email]).send()
        thongbao = f"{form.instance.full_name} book appointment with you on {form.instance.day_comes} at {form.instance.time_at}"
        if form.instance.technician != None:
            for empl in tech:
                if form.instance.technician == empl:
                    EmailMessage(self.chuDe, thongbao, to=[empl.email]).send()
        return redirect(self.success_url)



class Second(View):
    template = 'datHen/second.html'
    
    
    def get(self, request, pk):
        techDetail = get_object_or_404(Technician, id=pk)        
        secondForm = SecondStepForm()
        ngay = request.GET.get('day_comes')
        khach_da_hen = techDetail.get_clients().filter(day_comes=ngay).order_by('time_at')
        available = []
        available = techDetail.get_available(ngay=ngay)
        cont = {'techDetail': techDetail,
                'secondForm': secondForm,
                'hen': khach_da_hen,
                'available': available
            }
        
        return render(request, self.template, cont)
    
    
class FirstStep(View):
    template = 'datHen/first_step.html'
    tech = Technician.objects.all()
    def get(self,request):
        cont = {'tech': self.tech}
        return render(request, self.template, cont)
    
    
class Third(View):
    template = "datHen/third.html"
    success_url = reverse_lazy('datHen:listHen')
    
