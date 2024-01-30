from typing import Any
from django.shortcuts import render, redirect, get_object_or_404
from ledger.models import Khach, Technician
from django.views.generic import View, ListView
from django.urls import reverse_lazy
from .forms import DatHenFrom, ExistClientForm, SecondStepForm, ThirdForm, ThirdFormExist
from datetime import timedelta
from django.contrib import messages
from django.core.mail import EmailMessage
import datetime
from django.contrib.auth.mixins import LoginRequiredMixin



class DatHenView(LoginRequiredMixin,View):
    template_name = 'datHen/dathenview.html'
    def get(self, request):
        allTech = Technician.objects.filter(owner=request.user)
        # hnay = Khach.objects.filter(day_comes=datetime.datetime.today()).order_by("time_at")
        
        allKhachHen = {
            # 'khachHen': hnay,
                       'allTech': allTech,
                       }
        return render(request, self.template_name, allKhachHen)

# https://docs.djangoproject.com/en/5.0/ref/models/querysets/#field-lookups

    
class FindClient(View):
    template = 'datHen/exist_client_hen.html'
    def get(self, request):
        name = str(request.GET.get('full_name')).upper()
        khach = Khach.objects.filter(full_name=name,phone=request.GET.get('phone'))
        request.session['phone'] = ""
        request.session['full_name'] = ""
        form = ExistClientForm()
        request.session['phone'] = request.GET.get('phone')
        request.session['full_name'] = request.GET.get('full_name')
        cont = {'formDatHen': form, 'khach': khach}
        
        return render(request, self.template, cont)
    
class ExistFound(View):
    template = 'datHen/exist_found.html'
    
    def get(self, request, pk):
        request.session['client_id'] = ""
        tech = Technician.objects.all()
        cont = {'allTech': tech}
        request.session['client_id'] = pk
        return render(request, self.template, cont)
    
class ExistSecond(View):
    template = 'datHen/exist_second.html'
    def get(self, request, pk):
        request.session['tech_id'] = ""
        request.session['date'] = request.GET.get('day_comes')
        date = request.session['date']
        tech = get_object_or_404(Technician, id=pk)        
        secondForm = SecondStepForm()
        cont = {'tech': tech,
                'secondForm': secondForm,
                'ngay': date
            }
        request.session['tech_id'] = pk
        # request.session['day_comes'] = datetime.datetime.today().strftime("%Y-%m-%d")
        return render(request, self.template, cont)
    
class ExistThirdStep(View):
    chuDe = "Dayearns Confirm schedule"
    template = 'datHen/exist_third_step.html'
    success_url = reverse_lazy('ledger:index')
    
    def get(self,request):
        client_id = request.session['client_id']
        pk = request.session['tech_id']
        tech = get_object_or_404(Technician, id=pk)
        client = get_object_or_404(Khach, id=client_id)
        request.session['date'] = request.GET.get('day_comes')
        ngay = request.session['date']
        available = []
        available = tech.get_available(ngay=ngay)
        hen = tech.get_clients().filter(day_comes=ngay).order_by('time_at')
        form = ThirdFormExist(instance=client)
        form.instance.day_comes = ngay
        form.instance.technician = tech
        cont = {'form' : form, 
                'tech': tech,
                'available': available,
                'hen': hen,
                'ngay': ngay}
        
        return render(request, self.template, cont)
    
    def post(self,request):
        client_id = request.session['client_id']
        pk = request.session['tech_id']
        tech = get_object_or_404(Technician, id=pk)
        client = get_object_or_404(Khach, id=client_id)
        request.session['date'] = request.GET.get('day_comes')
        ngay = request.session['date']
        available = []
        available = tech.get_available(ngay=ngay)
        hen = tech.get_clients().filter(day_comes=ngay).order_by('time_at')
        form = ThirdFormExist(request.POST, instance=client)
        if not form.is_valid():
            cont = {'form' : form, 
                'tech': tech,
                'available': available,
                'hen': hen,
                'ngay': ngay}
            return render(request, self.template, cont)
        
        khac = form.save(commit=False)
        khac.day_comes = ngay
        khac.technician = tech
        khac.save()
        form.save_m2m()
        tinNhan = f"You scheduled with DayEarns \nOn: {form.instance.day_comes} \nAt: {form.instance.time_at} \nTechnician: {form.instance.technician}"
        messages.success(request, f"{form.instance.full_name} was scheduled successfully!")
        EmailMessage(self.chuDe, tinNhan, to=[form.instance.email]).send()
        thongbao = f"{form.instance.full_name} booked appointment with you on {form.instance.day_comes} at {form.instance.time_at}"
        if tech.email != None:
            EmailMessage(self.chuDe, thongbao, to=[tech.email]).send()
                    
        return redirect(self.success_url)


# class ExistFound(View):
#     template = 'datHen/layhen.html'
#     success_url = reverse_lazy('datHen:listHen')
#     chuDe = "Dayearns Confirm schedule"
#     def get(self, request, pk):
#         khach = get_object_or_404(Khach, id=pk)
#         request.session['client_id'] = pk
#         form = DatHenFrom(instance=khach)
#         cont = {'formDatHen': form}
#         return render(request, self.template, cont)
    
#     def post(self, request, pk):
#         tech = Technician.objects.all()
#         khach = get_object_or_404(Khach, id=pk)
#         form = DatHenFrom(request.POST, instance=khach)
#         if not form.is_valid():
#             cont = {'formDatHen': form}
#             return render(request, self.template, cont)
#         khac = form.save(commit=False)
#         khac.save()
#         form.save_m2m()
#         if form.instance.status == "Cancel":
#             tinNhan = "You had canceled. Thanks!"
#         else:
#             tinNhan = f"You scheduled with DayEarns \nOn: {form.instance.day_comes} \nAt: {form.instance.time_at} \nTechnician: {form.instance.technician}"
#         messages.success(request, f"{form.instance.full_name} was scheduled successfully!")
#         EmailMessage(self.chuDe, tinNhan, to=[form.instance.email]).send()
#         thongbao = f"{form.instance.full_name} book appointment with you on {form.instance.day_comes} at {form.instance.time_at}"
#         if form.instance.technician != None:
#             for empl in tech:
#                 if form.instance.technician == empl:
#                     EmailMessage(self.chuDe, thongbao, to=[empl.email]).send()
#         return redirect(self.success_url)
    

    # this view for user
class KhachLayHen(LoginRequiredMixin,View):
    template = 'datHen/layhen.html'
    success_url = reverse_lazy('datHen:listHen')
    chuDe = "Dayearns Confirm schedule"
    
    def get(self, request):
        form = DatHenFrom()
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
        date = request.session['date']
        tech = get_object_or_404(Technician, id=pk)        
        secondForm = SecondStepForm()
        cont = {'tech': tech,
                'secondForm': secondForm,
                'ngay': date
            }
        request.session['id'] = pk
        # request.session['day_comes'] = datetime.datetime.today().strftime("%Y-%m-%d")
        return render(request, self.template, cont)
    

# client view
class ThirdStep(View):
    chuDe = "Dayearns Confirm schedule"
    template = 'datHen/third_step.html'
    success_url = reverse_lazy('ledger:index')
    
    def get(self,request):
        pk = request.session['id']
        tech = get_object_or_404(Technician, id=pk)
        request.session['date'] = request.GET.get('day_comes')
        ngay = request.session['date']
        available = []
        available = tech.get_available(ngay=ngay)
        hen = tech.get_clients().filter(day_comes=ngay).order_by('time_at')
        form = ThirdForm()
        
        form.instance.day_comes = ngay
        cont = {'form' : form, 
                'tech': tech,
                'available': available,
                'hen': hen,
                'ngay': ngay}
        form.instance.technician = tech
        return render(request, self.template, cont)
    
    def post(self,request):
        pk = request.session['id']
        tech = get_object_or_404(Technician, id=pk)
        request.session['date'] = request.GET.get('day_comes')
        ngay = request.session['date']
        available = []
        available = tech.get_available(ngay=ngay)
        hen = tech.get_clients().filter(day_comes=ngay).order_by('time_at')
        form = ThirdForm(request.POST)
        
        if not form.is_valid():
            cont = {'form' : form, 
                'tech': tech,
                'available': available,
                'hen': hen,
                'ngay': ngay}
            return render(request, self.template, cont)
        
        khac = form.save(commit=False)
        khac.day_comes = ngay
        khac.technician = tech
        khac.save()
        form.save_m2m()
        tinNhan = f"You scheduled with DayEarns \nOn: {form.instance.day_comes} \nAt: {form.instance.time_at} \nTechnician: {form.instance.technician}"
        messages.success(request, f"{form.instance.full_name} was scheduled successfully!")
        EmailMessage(self.chuDe, tinNhan, to=[form.instance.email]).send()
        thongbao = f"{form.instance.full_name} booked appointment with you on {form.instance.day_comes} at {form.instance.time_at}"
        if tech.email != None:
            EmailMessage(self.chuDe, thongbao, to=[tech.email]).send()
                    
        return redirect(self.success_url)

