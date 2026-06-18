from django.shortcuts import render, redirect, get_object_or_404
from .models import (Technician, Khach, Service, Chat, Like, Supply, KhachVisit, Price,
                     Complimentary, TechWorkDay, Day_Of_Week)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView, CreateView, TemplateView, DetailView
from django.views import View
from .forms import (ClientForm, TechForm, ServiceForm, TaiKhoanCreationForm, TechWorkDayForm,
                    VacationForm, ChatForm, KhachWalkin, SupplyForm, ContactForm)
from django.urls import reverse_lazy, reverse
from django.contrib.auth import login
from datetime import timedelta, datetime
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
import requests
import os
from django.db import IntegrityError
from django.db.models import Prefetch, F
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
import stripe
from . import utils

stripe.api_key = os.environ.get('stripe_secret_key')
            
class PrivacyPolicy(View):
    template = "privacy.html"
    def get(self, request):
        context = {'spaName': utils.tenSpa, "email": utils.privacyEmail}
        return render(request, self.template, context)
    
class Contact(View):
    receiveEmail = "info@elegantnail.net"
    template = "contact.html"
    def get(self, request):
        form = ContactForm()
        context = {'form': form}
        return render(request, self.template, context)
    def post(self, request):
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            try:
                sendemail = EmailMessage(
                    subject='Contact Form Submission',
                    body=f'Name: {name}\nPhone: {phone}\nEmail: {email}\nMessage: {message}',
                    from_email=self.receiveEmail,
                    to=[self.receiveEmail],
                    reply_to=[email]
                )
                sendemail.send()
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('ledger:index')
            except Exception as e:
                messages.error(request, f"Failed to send message: {str(e)}")
        return render(request, self.template, {'form': form})
                
        
class AllEmployee(LoginRequiredMixin,ListView):
    template = 'ledger/all_employee.html'
    def get(self,request):
        employee = Technician.objects.filter(owner=request.user).exclude(name="anyOne").order_by("time_come_in")
        sort_tech = sorted(list(employee), 
                           key= lambda tech: tech.get_services_today(),reverse=False
                           )
        for tech in sort_tech:
            if tech.time_come_in == None or tech.time_come_in.date() < timezone.now().date():
                tech.isWork = False
                tech.save()
        cont = {'employees': sort_tech }
        return render(request, self.template, cont)
              
class UpdateTech(LoginRequiredMixin, View):
    def post(self, request):
        try:
            tech_id = request.POST.get('tech_id') #tech_id have to match with ajax data.tech_id from template
            tech = Technician.objects.get(id=tech_id)
            tech.isWork = not tech.isWork  #toggle
            if tech.isWork:
                tech.time_come_in = timezone.now()
                tech.date_go_work = timezone.now().date()
            else:
                tech.time_come_in = None
            tech.save()
            time_come_in_str = tech.time_come_in.strftime('%H:%M') if tech.time_come_in else ''
            return JsonResponse({
                'success' : True,
                'isWork': tech.isWork,
                'time_come_in': time_come_in_str,
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
    success_url = reverse_lazy("ledger:add_service")
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
        #stripe product and service.stripe_product_id
        product = stripe.Product.create(name=ser.service)
        ser.stripe_product_id = product.id
        ser.save()
        
        stripe_price = stripe.Price.create(
            product=ser.stripe_product_id,
            unit_amount=int(ser.price * 100), # convert to cents
            currency='usd',
        )
        price = Price(service=ser, price=ser.price, stripe_price_id=stripe_price.id)
        price.save()
        form.save_m2m
        messages.success(request, f"{form.instance.service} was added successfully!")
        return redirect(self.success_url)
       
class SetWorkDayView(LoginRequiredMixin, CreateView):
    model = TechWorkDay
    form_class = TechWorkDayForm
    template_name = 'ledger/set_work_days.html'

    def get_success_url(self):
        tech_id = self.kwargs.get('pk')
        return reverse_lazy('ledger:workdays', kwargs={'pk': tech_id})

    def get_initial(self):
        tech = get_object_or_404(Technician, id=self.kwargs.get('pk'))
        return {
            'start_time': tech.start_work_at,
            'end_time': tech.end_work,
            'is_working': 'true',
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Set Work Days and Time"
        tech = get_object_or_404(Technician, id=self.kwargs.get('pk'))
        context['tech'] = tech
        recurring = TechWorkDay.objects.filter(tech=tech, date__isnull=True).order_by('day_of_week')
        context['recurring_days'] = recurring
        recurring_map = {day.day_of_week: day for day in recurring}
        week_schedule = []
        for dow, label in Day_Of_Week:
            entry = recurring_map.get(dow)
            week_schedule.append({
                'day_of_week': dow,
                'label': label,
                'entry': entry,
                'is_configured': entry is not None,
                'is_working': entry.is_working if entry else True,
                'start_time': (entry.start_time if entry and entry.start_time else tech.start_work_at),
                'end_time': (entry.end_time if entry and entry.end_time else tech.end_work),
            })
        context['week_schedule'] = week_schedule
        recurring_off_days = []
        for day in week_schedule:
            if not day['is_working'] and day['is_configured']:
                recurring_off_days.append(day['label'])
        context['recurring_off_days'] = recurring_off_days
        today = timezone.now().date()
        specific = (
            TechWorkDay.objects
            .filter(tech=tech, date__isnull=False)
            .exclude(notes__icontains='Bulk')
            .order_by('date')
        )
        context['specific_exceptions'] = specific
        context['today'] = today
        context['upcoming_exceptions'] = specific.filter(date__gte=today)
        return context

    def form_valid(self, form):
        tech = get_object_or_404(Technician, id=self.kwargs.get('pk'))
        date = form.cleaned_data.get('date')
        day_of_week = form.cleaned_data['day_of_week']
        is_working = form.cleaned_data.get('is_working', True)
        start_time = form.cleaned_data.get('start_time')
        end_time = form.cleaned_data.get('end_time')

        if is_working:
            start_time = start_time or tech.start_work_at
            end_time = end_time or tech.end_work
        else:
            start_time = None
            end_time = None

        try:
            if date:
                TechWorkDay.objects.update_or_create(
                    tech=tech,
                    date=date,
                    defaults={
                        'day_of_week': date.weekday(),
                        'is_working': is_working,
                        'start_time': start_time,
                        'end_time': end_time,
                    },
                )
                msg = f"Schedule for {date.strftime('%A, %b %d')} saved for {tech.name}."
            else:
                TechWorkDay.objects.update_or_create(
                    tech=tech,
                    day_of_week=day_of_week,
                    date=None,
                    defaults={
                        'is_working': is_working,
                        'start_time': start_time,
                        'end_time': end_time,
                    },
                )
                work_days = list(tech.work_days.ljust(7, '1')[:7])
                work_days[day_of_week] = '1' if is_working else '0'
                tech.work_days = ''.join(work_days)
                tech.save(update_fields=['work_days'])
                day_label = dict(TechWorkDay._meta.get_field('day_of_week').choices).get(day_of_week, '')
                if is_working:
                    msg = f"{day_label} is back on ({start_time} - {end_time}) for {tech.name}."
                else:
                    msg = f"{day_label} is off every week for {tech.name} until you turn it back on."
            messages.success(self.request, msg)
            return redirect(self.get_success_url())
        except IntegrityError:
            form.add_error(None, "Could not save this schedule. Please try again.")
            return self.form_invalid(form)

        
class DeleteWorkDayView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            work_day = get_object_or_404(TechWorkDay, id=request.POST.get('work_day_id'))
            work_day.delete()
            return JsonResponse({'success': True, 'message': 'Work day deleted successfully.'}, status=200)
        except TechWorkDay.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Work day not found.'}, status=404)

class TechVacationView(LoginRequiredMixin, UpdateView):
    model = Technician
    form_class = VacationForm
    template_name = 'ledger/vacation_tech.html'
    success_url = reverse_lazy("datHen:listHen")

    def get_object(self):
        return get_object_or_404(Technician, id=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Off Period (consecutive days)"
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get('clear_vacation'):
            tech = self.get_object()
            tech.vacation_start = None
            tech.vacation_end = None
            tech.save(update_fields=['vacation_start', 'vacation_end'])
            messages.success(request, f"{tech.name} is turned back on.")
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(
            self.request,
            f"Off period saved for {form.instance.name}."
            + (" Stays off until you turn back on." if not form.instance.vacation_end else "")
        )
        return super().form_valid(form)

class ChatView(View):
    template = "ledger/chat_room.html"
    def get(self, request, pk):
        request.session['client_id'] = pk
        client = get_object_or_404(Khach, id=pk)
        allChat = Chat.objects.filter(reply_to__isnull=True).order_by('-created_at').select_related("client").prefetch_related(
            Prefetch('likes', queryset=Like.objects.filter(client=client), to_attr='current_client_like'),
        )
        allChat = allChat[:75]
        paginator = Paginator(allChat, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        chat_form = ChatForm()
        context = {
            'page_obj' : page_obj, 'chat_form': chat_form, 'client' : client
        }
        return render(request, self.template, context)
    
class ChatLikeView(View):
    def post(sefl, request, chat_id):
        client_id = request.session.get('client_id')
        if not client_id:
            return JsonResponse({'error': "client not found"}, status=400)
        client = get_object_or_404(Khach, id=client_id)
        chat = get_object_or_404(Chat, id= chat_id)
        chat.view_count = F('view_count') + 1
        chat.save(update_fields=['view_count'])
        like, create = Like.objects.get_or_create(chat=chat, client=client)
        if not create:
            like.delete()
            liked = False
        else:
            liked = True
        total_likes = chat.total_likes
        return JsonResponse({
            'liked' : liked,
            'total_likes': total_likes
        })

@require_POST
def chatDetailLike(request, chat_id):
    client_id = request.session.get('client_id')
    if not client_id:
        return JsonResponse({'error': "client not found"}, status=400)
    client = get_object_or_404(Khach, id=client_id)
    chat = get_object_or_404(Chat, id= chat_id)
    chat.view_count = F('view_count') + 1
    chat.save(update_fields=['view_count'])
    like, create = Like.objects.get_or_create(chat=chat, client=client)
    if not create:
        like.delete()
        liked = False
    else:
        liked = True
    total_likes = chat.total_likes
    return JsonResponse({
        'liked' : liked,
        'total_likes': total_likes
    })
        
class ChatUserLikeView(LoginRequiredMixin, View):
    def post(sefl, request, chat_id):
        chu_trang = request.user
        chat = get_object_or_404(Chat, id= chat_id)
        chat.view_count = F('view_count') + 1
        chat.save(update_fields=['view_count'])
        like, create = Like.objects.get_or_create(chat=chat, owner=chu_trang)
        if not create:
            like.delete()
            liked = False
        else:
            liked = True
            chat.isNew = False
            chat.save()
        total_likes = chat.total_likes
        return JsonResponse({
            'liked' : liked,
            'total_likes': total_likes
        })
        
class ChatDetailView(View):
    template = "ledger/chat_detail.html"
    def get(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        Chat.objects.filter(id=pk).update(view_count=F('view_count') + 1)
        khach_id = request.session['client_id']
        khach = get_object_or_404(Khach, id=khach_id)
        replies = Chat.objects.filter(reply_to=chat).order_by('created_at').select_related("client").prefetch_related(
            Prefetch('likes', queryset=Like.objects.filter(client=khach), to_attr="current_khach_like")
        )
        context = {
            'khach_id' : khach_id,
            'client': khach,
            'chat' : chat,
            'replies': replies,
            'chat_form' : ChatForm()
        }
        return render(request, self.template, context)
    
    def post(self, request, pk):
        khach_id = request.session['client_id']
        khach_moi = get_object_or_404(Khach, id=khach_id)
        chat = get_object_or_404(Chat, id=pk)
        chat.view_count = F('view_count') + 1
        chat.save(update_fields=['view_count'])
        form = ChatForm(request.POST)
        replies = Chat.objects.filter(reply_to=chat).order_by('created_at')
        if form.is_valid():
            new_chat = form.save(commit=False)
            new_chat.client = khach_moi
            new_chat.reply_to = chat
            new_chat.save()
            return redirect('ledger:chat_detail', pk=pk)
        context = {
            'chat' : chat,
            'replies': replies,
            'chat_form' : form
        }
        return render(request, self.template, context)

class ChatCreateView(View):
    def post(self, request, pk):
        client = get_object_or_404(Khach, id=pk)
        chat = Chat(text=request.POST['text'], client=client)
        chat.save()
        return redirect(reverse('ledger:chat_room', args=[pk]))

@require_POST
def chat_delete(request, pk):
    if 'client_id' not in request.session:
        return JsonResponse({
            'success': False,
            'error' : "Client not identified."
        }, status=403)
    client_id = request.session['client_id']
    chat = get_object_or_404(Chat, id=pk)
    if chat.client_id != client_id:
        return JsonResponse({
            'success': False,
            'error' : "You don't have permisson to delete this post."
        }, status=403)
    chat.delete()
    return JsonResponse({
            'success': True,
        })
    
class UserChatView(LoginRequiredMixin, View):
    template = "ledger/user_chat_room.html"
    def get(self, request):
        chu_tai_khoan = request.user
        allChat = Chat.objects.filter(reply_to__isnull=True).order_by('-created_at').select_related("client").prefetch_related(
            Prefetch('likes', queryset=Like.objects.filter(owner=chu_tai_khoan), to_attr='current_owner_like')
        )
        allChat = allChat[:100]
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
        Chat.objects.filter(id=pk).update(view_count=F('view_count') + 1)
        chu_tai_khoan = request.user
        if chat.isNew:
            chat.isNew = False
            chat.save()
        replies = Chat.objects.filter(reply_to=chat).order_by('-created_at').select_related("client").prefetch_related(
            Prefetch('likes', queryset=Like.objects.filter(owner=chu_tai_khoan), to_attr='current_owner_like')
        )
        context = {
            'chat' : chat,
            'replies': replies,
            'chat_form' : ChatForm()
        }
        return render(request, self.template, context)
    
    def post(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        chat.view_count = F('view_count') + 1
        chat.save(update_fields=['view_count'])
        form = ChatForm(request.POST)
        replies = Chat.objects.filter(reply_to=chat).order_by('created_at')
        if form.is_valid():
            new_chat = form.save(commit=False)
            new_chat.owner = request.user
            new_chat.reply_to = chat
            new_chat.save()
            return redirect('ledger:user_chat_detail', pk=pk)
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
    template = "home.html"
    allService = Service.objects.all()
    nail = allService.filter(category="Nail Enhancement")
    mani = allService.filter(category="Manicure")
    feet = allService.filter(category="Pedicure")
    wax = allService.filter(category="Wax")

    def get(self, request):
        complimentaries = Complimentary.objects.filter(is_available=True).exclude(category=Complimentary.Category.gift).order_by('category')
        today = timezone.now().date()
        allTech = Technician.objects.filter(is_accept_booking=True).exclude(name="anyOne")
        context = {
            'nails': self.nail,
            'feets': self.feet,
            'waxs': self.wax,
            'mani': self.mani,
            'allTech': allTech,
            'complimentaries': complimentaries,
            'today': today,
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
        dv = form.cleaned_data['services']
        existing_client = form.cleaned_data.get('existing_client')
        ngay = timezone.now().today().date()
        thoigian = timezone.now().time()
        if existing_client:
            khach = existing_client
            khach.day_comes = ngay
            khach.time_at = thoigian
            khach.status = Khach.Status.anyone
            khach.technician = Technician.objects.get(owner=self.request.user, name="anyOne")
            khach.save()
            
        else:
            khach, _ = Khach.objects.get_or_create(
                full_name=full_name,
                phone=phone,
                defaults={
                    'day_comes': ngay,
                    'time_at': thoigian,
                    'technician': Technician.objects.get(owner=self.request.user, name="anyOne"),
                }
            )
        khach.services.set(dv)    
        form.instance = khach
        if not khach.today_visit:
            utils.saveKhachVisit(khach, ngay,thoigian,dv, khach.technician, KhachVisit.Status.anyone)
        messages.success(self.request, f"Welcom {form.instance.full_name} to our salon!")
        return super().form_valid(form)

def services_info(request, category):
    template = "ledger/services_info.html"
    allServices = Service.objects.filter(category=category).exclude(service='tax')
    return render(request, template, {'allServices': allServices, 'category': category})
    

class SupplyCreateView(LoginRequiredMixin, CreateView):
    template_name = "ledger/supply_create.html"
    model = Supply
    form_class = SupplyForm
    success_url = reverse_lazy('ledger:supply_create')
    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f"{form.instance.title} has been added to the supply list.")
        return super().form_valid(form)
    
class AllSupply(LoginRequiredMixin, ListView):
    model = Supply
    template_name = "ledger/all_supplies.html"
    ordering = ['-is_wanted', '-date']


@require_POST
def supplyWanted(request, supply_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'you need to login'}, status=401)
    supply = get_object_or_404(Supply, id=supply_id)
    supply.is_wanted = not supply.is_wanted
    supply.save()
    return JsonResponse({'success': True, 'is_wanted': supply.is_wanted}, status=200)
    
def supplyDelete(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'You need to login first'}, status=401)
    supply = get_object_or_404(Supply, id=pk)
    supply.delete()
    return JsonResponse({'success': True}, status=200)

class EmployeeBio(DetailView):
    template = "ledger/employee_bio.html"
    
    def get(self, request, pk):
        employee = get_object_or_404(Technician, id=pk)
        Technician.objects.filter(id=pk).update(view_count=F('view_count') + 1)
        work_days = TechWorkDay.objects.filter(tech=employee, date__isnull=True).order_by('day_of_week')
        context = {'employee': employee, 'work_days': work_days}
        return render(request, self.template, context)
    
    