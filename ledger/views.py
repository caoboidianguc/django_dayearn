from django.shortcuts import render, redirect, get_object_or_404
from .models import Technician, Khach, Service, Chat
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.views import View
from .forms import (ClientForm, TechForm, ServiceForm, TaiKhoanCreationForm, 
                    VacationForm, ChatForm, KhachWalkin)
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login
from datetime import timedelta
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
import requests
import os


class AllEmployee(LoginRequiredMixin,ListView):
    template = 'ledger/all_employee.html'
    def get(self,request):
        today = timezone.now().date()
        employee = Technician.objects.filter(owner=request.user).order_by("time_come_in")
        sort_tech = sorted(list(employee), 
                           key= lambda tech: tech.get_services_today(),reverse=False
                           )
        cont = {'employees': sort_tech }
        return render(request, self.template, cont)
              
class UpdateTech(LoginRequiredMixin, View):
    def post(self, request):
        try:
            tech_id = request.POST.get('tech_id') #tech_id have to match with ajax data.tech_id from template
            tech = Technician.objects.get(id=tech_id)
            tech.isWork = not tech.isWork  #toggle
            if tech.isWork:
                tech.time_come_in = timezone.now().strftime('%H:%M')
                tech.date_go_work = timezone.now().date()
            else:
                tech.time_come_in = None
            tech.save()
            return JsonResponse({
                'success' : True,
                'isWork': tech.isWork,
                'time_come_in': tech.time_come_in if tech.isWork else '',
                'color': 'green' if tech.isWork else 'gray'
            })
        except Technician.DoesNotExist:
            return JsonResponse({
                'success' : False,
                'error': 'Technician not found'
            }, status=404)
       

class AllServices(LoginRequiredMixin, ListView):
    
    template = 'ledger/list_services.html'
    def get(self, request):
        serv = Service.objects.filter(owner=request.user).order_by('category')
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
        form = TechForm(request.POST, request.FILES)
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
    success_url = reverse_lazy('ledger:all_employee')
    
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
        context = {'form': form}
        return render(request, self.template, context)
    
    def post(self, request):
        form = ServiceForm(request.POST)
        if not form.is_valid():
            cont = {'form': form}
            return render(request, self.template, cont)
        ser = form.save(commit=False)
        ser.owner = self.request.user
        ser.save()
        form.save_m2m
        return redirect(self.success_url)
       

class TechVacationView(LoginRequiredMixin,UpdateView):
    model = Technician
    form_class = VacationForm
    template_name = 'ledger/vacation_tech.html'
    success_url = reverse_lazy("datHen:listHen")
    def get_object(self):
        return get_object_or_404(Technician, id=self.kwargs.get('pk'))
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Set Vacation Time"
        return context
    
class ChatView(View):
    template = "ledger/chat_room.html"
    def get(self, request, pk):
        request.session['client_id'] = pk
        client = get_object_or_404(Khach, id=pk)
        allChat = Chat.objects.filter(reply_to__isnull=True).order_by('-created_at').select_related("client")
        allChat = allChat[:75]
        paginator = Paginator(allChat, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        chat_form = ChatForm()
        context = {
            'page_obj' : page_obj, 'chat_form': chat_form, 'client' : client
        }
        return render(request, self.template, context)

class ChatDetailView(View):
    template = "ledger/chat_detail.html"
    def get(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        replies = Chat.objects.filter(reply_to=chat).order_by('created_at')
        khach_id = request.session['client_id']
        context = {
            'khach_id' : khach_id,
            'chat' : chat,
            'replies': replies,
            'chat_form' : ChatForm()
        }
        return render(request, self.template, context)
    
    def post(self, request, pk):
        khach_id = request.session['client_id']
        khach_moi = get_object_or_404(Khach, id=khach_id)
        chat = get_object_or_404(Chat, id=pk)
        form = ChatForm(request.POST)
        replies = Chat.objects.filter(reply_to=chat).order_by('created_at')
        if form.is_valid():
            new_chat = form.save(commit=False)
            # new_chat.owner = request.user
            new_chat.client = khach_moi
            new_chat.reply_to = chat
            new_chat.save()
            return redirect('ledger:chat_detail', pk=pk)
        context = {
            'chat' : chat,
            'replies': replies,  # Fetch replies again
            'chat_form' : form
        }
        return render(request, self.template, context)

class ChatCreateView(View):
    def post(self, request, pk):
        client = get_object_or_404(Khach, id=pk)
        chat = Chat(text=request.POST['text'], client=client)
        chat.save()
        return redirect(reverse('ledger:chat_room', args=[pk]))
    
class UserChatView(LoginRequiredMixin, View):
    template = "ledger/user_chat_room.html"
    def get(self, request):
        allChat = Chat.objects.filter(reply_to__isnull=True).order_by('created_at').select_related("client")
        allChat = allChat[:75]
        paginator = Paginator(allChat, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        chat_form = ChatForm()
        context = {
            'page_obj' : page_obj, 'chat_form': chat_form,
        }
        return render(request, self.template, context)

class UserChatCreateView(LoginRequiredMixin, View):
    def post(self, request):
        chat = Chat(text=request.POST['text'], owner=request.user)
        chat.save()
        return redirect(reverse('ledger:user_chat_room'))
    
class UserChatDetailView(LoginRequiredMixin, View):
    template = "ledger/user_chat_detail.html"
    def get(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        replies = Chat.objects.filter(reply_to=chat).order_by('-created_at')
        context = {
            'chat' : chat,
            'replies': replies,
            'chat_form' : ChatForm()
        }
        return render(request, self.template, context)
    
    def post(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        form = ChatForm(request.POST)
        replies = Chat.objects.filter(reply_to=chat).order_by('created_at')
        if form.is_valid():
            new_chat = form.save(commit=False)
            new_chat.owner = request.user
            new_chat.reply_to = chat
            new_chat.save()
            return redirect('ledger:chat_detail', pk=pk)
        context = {
            'chat' : chat,
            'replies': replies,  # Fetch replies again
            'chat_form' : form
        }
        return render(request, self.template, context)

class ServiceDetail(LoginRequiredMixin, View):
    template = "ledger/service_detail.html"
    def get(self, request, pk):
        service = get_object_or_404(Service, id=pk)
        form = ServiceForm(instance=service)
        context = {'service': service,
                   'form': form}
        return render(request, self.template, context)
    
    def post(self, request, pk):
        service = get_object_or_404(Service, id=pk)
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f"{form.instance.service} was updated successfully!")
            return redirect(reverse('ledger:services'))
        context = {'service': service,
                   'form': form}
        return render(request, self.template, context)
    


class CustomerVisit(View):
    page_id = "4841897016034853"
    access_token = os.environ.get('access_token')
    url = f"https://graph.facebook.com/v22.0/{page_id}/feed?fields=full_picture,message,attachments{{media,image}}&access_token={access_token}"
    template = "home.html"
    allService = Service.objects.all()
    nail = allService.filter(category="Nail Enhancement")
    mani = allService.filter(category="Manicure")
    feet = allService.filter(category="Pedicure")
    wax = allService.filter(category="Wax")

    def get(self, request):
        response = requests.get(self.url)
        if response.status_code == 200:
            data = response.json()
            latest_image_urls = []
            for post in data.get('data', []):
                if 'full_picture' in post:
                    latest_image_urls.append(post['full_picture'])
                # if 'attachments' in post and post['attachments']['data']:
                #     for attachment in post['attachments']['data']:
                #         if 'media' in attachment:
                #             for media in attachment['media']:
                #                 if isinstance(media, dict) and 'image' in media and isinstance(media['image'], dict):
                #                     latest_image_urls.append(media['image']['src'])
            latest_image_urls = latest_image_urls[:3]
                        
            context = {
                'nails': self.nail,
                'feets': self.feet,
                'waxs': self.wax,
                'mani': self.mani,
                'latest_image_urls': latest_image_urls,
            }
        else:
            print(f"Failed to fetch data: {response.status_code}")
            context = {
                'nails': self.nail,
                'feets': self.feet,
                'waxs': self.wax,
                'mani': self.mani,
                'latest_image_urls': [],
            }
        return render(request, self.template, context)
    
class ClientWalkinView(LoginRequiredMixin, CreateView):
    template_name = "ledger/walkin.html"
    form_class = KhachWalkin
    model = Khach
    success_url = reverse_lazy('ledger:walkin')
    def form_valid(self, form):
        full_name = form.cleaned_data['full_name'].upper()
        phone = form.cleaned_data['phone']
        existing_client = form.cleaned_data.get('existing_client')
        if existing_client:
            khach = existing_client
            khach.day_comes = timezone.now().today().date()
            khach.time_at = timezone.now().time()
            khach.status = Khach.Status.anyone
            khach.technician = Technician.objects.get(owner=self.request.user, name="anyOne")
            khach.save()
        else:
            khach, _ = Khach.objects.get_or_create(
                full_name=full_name,
                phone=phone,
                defaults={
                    'day_comes': timezone.now().today().date(),
                    'time_at': timezone.now().time(),
                    'technician': Technician.objects.get(owner=self.request.user, name="anyOne"),
                }
            )
            
        form.instance = khach
        messages.success(self.request, f"Welcom {form.instance.full_name} to our salon!")
        return super().form_valid(form)
    

