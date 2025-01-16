from django.shortcuts import render, redirect, get_object_or_404
from .models import Technician, Khach, Service
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.views import View
from .forms import ClientForm, TechForm, ServiceForm, TaiKhoanCreationForm, TurnForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login
from datetime import timedelta
from django.contrib import messages
from django.http import HttpResponse


class AllEmployee(LoginRequiredMixin,ListView):
    template = 'ledger/index.html'
    def get(self,request):
        # employee = Technician.objects.all()
        employee = Technician.objects.filter(owner=request.user)
        cont = {'employees': employee }
        return render(request, self.template, cont)
              
          
          
class AllServices(LoginRequiredMixin, ListView):
    
    template = 'ledger/list_services.html'
    def get(self, request):
        serv = Service.objects.filter(owner=request.user)
        cont = {'dvu': serv}
        return render(request, self.template, cont)
    
class EmpCreate(LoginRequiredMixin, View):
    template = 'ledger/add_employee.html'
    success_url = reverse_lazy('ledger:add_employee')
    def get(self,request):
        form = TechForm()
        contx = {'form': form}
        return render(request, self.template, contx)
    def post(self, request):
        form = TechForm(request.POST)
        if not form.is_valid():
            cont = {'form': form}
            return render(request, self.template, cont)
        emp = form.save(commit=False)
        emp.owner = self.request.user
        emp.save()
        form.save_m2m
        messages.success(request, f"{form.instance.name} was created successfully!")
        return redirect(self.success_url)
    
    
class TaoTaiKhoan(View):
    template = "ledger/user_form.html"
    success_url = reverse_lazy('ledger:home')
    
    def get(self, request):
        form = TaiKhoanCreationForm()
        cont = {'form': form }
        return render(request, self.template, cont)
    def post(self, request):
        form = TaiKhoanCreationForm(request.POST)
        if form.is_valid():
            ten = form.save()
            login(request, ten)
            return redirect(self.success_url)

class AddService(LoginRequiredMixin, View):
    template = "ledger/service_form.html"
    success_url = reverse_lazy("ledger:services")
    def get(self, request):
        form = ServiceForm()
        cont = {'form': form}
        return render(request, self.template, cont)
    def post(self, request):
        form = ServiceForm(request.POST)
        if not form.is_valid():
            cont = {'form': form}
            return render(request, self.template, cont)
        # form.instance.thoiGian = timedelta(minutes=45)
        ser = form.save(commit=False)
        ser.owner = self.request.user
        ser.save()
        form.save_m2m
        return redirect(self.success_url)
   
class EmployeeTurn(View):
    temp = "ledger/index.html"
    success_url = reverse_lazy("ledger:tech_turn")
    def get(self, request):
        form = TurnForm()
        cont = {'form': form}
        return render(request, self.temp, cont)
    
    def post(self,request):
        form = TurnForm(request.POST)
        if not form.is_valid():
            cont = {'form': form}
            return render(request, self.temp, cont)
        turn = form.save(commit=False)
        turn.save()
        form.save_m2m
        return redirect(self.success_url)
        

class CustomerVisit(View):
    template = "home.html"
    def get(self, request):
        return render(request, self.template)
    def post(self, request):
        pass

