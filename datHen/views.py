from typing import Any
from django.shortcuts import render, redirect, get_object_or_404
from ledger.models import Khach, Technician, Service, KhachVisit
from django.views.generic import View
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import (UserExistClientForm, ExistClientForm, DateForm, ThirdForm, DatHenForm,
                    ThirdFormExist, ServicesChoiceForm, KhachDetailForm, VisitForm, DatePickerInput)
from datetime import timedelta, date, datetime, time
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import JsonResponse
from ledger import utils

# Timeline display: pixels per minute of shop-open hours.
# 2.0 → ~30px per 15 minutes.
_TIMELINE_PX_PER_MIN = 2.0
_TIMELINE_MIN_BLOCK_MINUTES = 15
_TIMELINE_SLOT_STEP_MINUTES = 30
# Minor grid every 15 minutes (labels stay every 30)
_TIMELINE_MINOR_STEP_MINUTES = 15
_DEFAULT_OPEN = time(9, 30)
_DEFAULT_CLOSE = time(18, 30)

def _time_to_minutes(t):
    """Convert a time (or datetime.time) to minutes since midnight."""
    return t.hour * 60 + t.minute


def _minutes_to_time(total_minutes):
    total_minutes = int(total_minutes) % (24 * 60)
    return time(hour=total_minutes // 60, minute=total_minutes % 60)


def _format_time_label(t):
    """12-hour label without leading zero on the hour (portable across OSes)."""
    return t.strftime('%I:%M %p').lstrip('0')


def _pct_from_timeline(t, timeline_start_min, total_minutes):
    if total_minutes <= 0:
        return 0.0
    return max(0.0, min(100.0, (_time_to_minutes(t) - timeline_start_min) / total_minutes * 100))


def _build_timeline_slots(timeline_start, timeline_end, step_minutes=_TIMELINE_SLOT_STEP_MINUTES):
    """Hour/half-hour labels for the left gutter of the schedule board."""
    start_min = _time_to_minutes(timeline_start)
    end_min = _time_to_minutes(timeline_end)
    total = end_min - start_min
    if total <= 0:
        return []
    slots = []
    current = start_min
    # Snap first label to a step boundary if needed, but always include open.
    while current <= end_min:
        t = _minutes_to_time(current)
        slots.append({
            'time': t,
            'label': _format_time_label(t),
            'top_pct': _pct_from_timeline(t, start_min, total),
        })
        current += step_minutes
    # Ensure close time appears if last step skipped it
    if not slots or slots[-1]['time'] != timeline_end:
        slots.append({
            'time': timeline_end,
            'label': _format_time_label(timeline_end),
            'top_pct': 100.0,
        })
    return slots


def _build_timeline_minor_lines(timeline_start, timeline_end, step_minutes=_TIMELINE_MINOR_STEP_MINUTES):
    """Light 15-minute grid lines (no labels) for finer time reading."""
    start_min = _time_to_minutes(timeline_start)
    end_min = _time_to_minutes(timeline_end)
    total = end_min - start_min
    if total <= 0:
        return []
    lines = []
    current = start_min
    while current <= end_min:
        t = _minutes_to_time(current)
        is_major = (current - start_min) % _TIMELINE_SLOT_STEP_MINUTES == 0
        lines.append({
            'top_pct': _pct_from_timeline(t, start_min, total),
            'is_major': is_major,
        })
        current += step_minutes
    return lines


def _annotate_visit_position(visit, timeline_start_min, total_minutes):
    """Attach top_pct / height_pct so the template can place the appointment block."""
    start_min = _time_to_minutes(visit.time_at)
    try:
        done = visit.get_done_at()
    except Exception:
        done = visit.time_at
    end_min = _time_to_minutes(done)
    duration = max(end_min - start_min, _TIMELINE_MIN_BLOCK_MINUTES)
    visit.done_at_display = done
    visit.top_pct = _pct_from_timeline(visit.time_at, timeline_start_min, total_minutes)
    if total_minutes > 0:
        visit.height_pct = max(duration / total_minutes * 100, _TIMELINE_MIN_BLOCK_MINUTES / total_minutes * 100)
        # Keep block inside the lane
        if visit.top_pct + visit.height_pct > 100:
            visit.height_pct = max(1.0, 100 - visit.top_pct)
    else:
        visit.height_pct = 5.0
    return visit


def _free_gaps_for_tech(clients, work_start, work_end, timeline_start_min, total_minutes):
    """
    Empty windows between appointments (and before first / after last) inside the tech's work hours.
    Shown as free bands so staff can see when another client can be scheduled.
    """
    if not work_start or not work_end or total_minutes <= 0:
        return []
    active = [
        c for c in clients
        if getattr(c, 'status', None) != KhachVisit.Status.cancel
    ]
    active.sort(key=lambda c: c.time_at)
    gaps = []
    cursor = work_start

    def add_gap(gap_start, gap_end):
        start_m = _time_to_minutes(gap_start)
        end_m = _time_to_minutes(gap_end)
        if end_m - start_m < 5:
            return
        gaps.append({
            'start': gap_start,
            'end': gap_end,
            'top_pct': _pct_from_timeline(gap_start, timeline_start_min, total_minutes),
            'height_pct': max((end_m - start_m) / total_minutes * 100, 0.5),
            'label': f"{_format_time_label(gap_start)} – {_format_time_label(gap_end)}",
        })

    for visit in active:
        try:
            done = visit.get_done_at()
        except Exception:
            done = visit.time_at
        if visit.time_at > cursor:
            gap_end = min(visit.time_at, work_end) if visit.time_at < work_end else work_end
            if cursor < gap_end:
                add_gap(cursor, gap_end)
        if done > cursor:
            cursor = done
        if cursor >= work_end:
            break
    if cursor < work_end:
        add_gap(max(cursor, work_start), work_end)
    return gaps


def _booking_restart(request, message):
    messages.error(request, message)
    return redirect('datHen:first_step')


def _parse_booking_date(date_value):
    if not date_value:
        return None
    if hasattr(date_value, 'year'):
        return date_value
    return datetime.strptime(str(date_value), '%Y-%m-%d').date()


def _get_service_ids(request):
    service_ids = (
        request.POST.getlist('service_ids')
        or request.GET.getlist('dichvu')
        or request.session.get('service_ids', [])
    )
    parsed = []
    for service_id in service_ids:
        try:
            parsed.append(int(service_id))
        except (TypeError, ValueError):
            continue
    return parsed


def _get_selected_services(request):
    service_ids = _get_service_ids(request)
    if not service_ids:
        return Service.objects.none()
    return Service.objects.filter(id__in=service_ids)


def _service_duration_minutes(services):
    if not services:
        return 0
    return sum(service.time_perform.total_seconds() for service in services) / 60


def _available_times(tech, booking_date, services):
    time_perform = _service_duration_minutes(services)
    available = list(tech.get_available_with(ngay=booking_date, thoigian=time_perform))
    if booking_date == date.today():
        cutoff = datetime.now() + timedelta(minutes=30)
        available = [slot for slot in available if slot > cutoff.time()]
    return available


def _annotate_tech_off_notices(techs):
    for tech in techs:
        tech.off_notices = tech.get_booking_off_notices()


def _third_step_context(state):
    available = state['available']
    unavailability = state['tech'].get_unavailability_reason(
        state['booking_date'],
        available,
    )
    return {
        'tech': state['tech'],
        'available': available,
        'ngay': state['booking_date'],
        'allServices': state['services'],
        'unavailability': unavailability,
    }


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
        form = DatePickerInput(initial={'date': selected_date})
        prev_day = selected_date - timedelta(days=1)
        next_day = selected_date + timedelta(days=1)
        all_tech = Technician.objects.filter(owner=request.user).order_by('time_come_in')
        now_time = timezone.now().time()

        # Collect work windows so the board opens at earliest open / closes at latest close
        day_starts = []
        day_ends = []
        for tech in all_tech:
            tech.on_vacation = tech.is_on_vacation(check_date=selected_date)
            tech.is_day_off = tech.get_day_off(check_date=selected_date)
            tech.off_for_date = tech.on_vacation or tech.is_day_off
            work_start, work_end = tech.get_effective_work_hours(selected_date)
            tech.work_start = work_start
            tech.work_end = work_end
            if work_start and work_end and not tech.off_for_date:
                day_starts.append(work_start)
                day_ends.append(work_end)
            tech.clients = list(
                tech.get_khachVisit()
                .filter(day_comes=selected_date)
                .select_related('client', 'technician')
                .prefetch_related('services')
                .order_by('time_at')
            )

        timeline_start = min(day_starts) if day_starts else _DEFAULT_OPEN
        timeline_end = max(day_ends) if day_ends else _DEFAULT_CLOSE
        # If any visit falls outside work hours, expand the board so it still shows
        for tech in all_tech:
            for visit in tech.clients:
                if visit.time_at < timeline_start:
                    timeline_start = visit.time_at
                try:
                    done = visit.get_done_at()
                except Exception:
                    done = visit.time_at
                if done > timeline_end:
                    timeline_end = done

        timeline_start_min = _time_to_minutes(timeline_start)
        timeline_end_min = _time_to_minutes(timeline_end)
        total_minutes = max(timeline_end_min - timeline_start_min, 1)
        lane_height_px = int(total_minutes * _TIMELINE_PX_PER_MIN)

        for tech in all_tech:
            for visit in tech.clients:
                _annotate_visit_position(visit, timeline_start_min, total_minutes)
                visit.is_past = visit.get_done_at() < now_time if selected_date == timezone.now().date() else (
                    selected_date < timezone.now().date()
                )
            if tech.off_for_date or not tech.work_start:
                tech.free_gaps = []
            else:
                tech.free_gaps = _free_gaps_for_tech(
                    tech.clients,
                    tech.work_start,
                    tech.work_end,
                    timeline_start_min,
                    total_minutes,
                )
            # Grey “outside this tech’s hours” bands relative to the shared timeline
            tech.outside_before_pct = 0.0
            tech.outside_after_top_pct = 100.0
            tech.outside_after_height_pct = 0.0
            if tech.work_start and tech.work_end and not tech.off_for_date:
                tech.outside_before_pct = _pct_from_timeline(
                    tech.work_start, timeline_start_min, total_minutes
                )
                after_top = _pct_from_timeline(tech.work_end, timeline_start_min, total_minutes)
                tech.outside_after_top_pct = after_top
                tech.outside_after_height_pct = max(0.0, 100.0 - after_top)

        now_pct = None
        if selected_date == timezone.now().date():
            if timeline_start <= now_time <= timeline_end:
                now_pct = _pct_from_timeline(now_time, timeline_start_min, total_minutes)

        context = {
            'allTech': all_tech,
            'selected_date': selected_date,
            'prev_day': prev_day,
            'next_day': next_day,
            'form': form,
            'now': now_time,
            'timeline_start': timeline_start,
            'timeline_end': timeline_end,
            'timeline_slots': _build_timeline_slots(timeline_start, timeline_end),
            'timeline_minor_lines': _build_timeline_minor_lines(timeline_start, timeline_end),
            'lane_height_px': lane_height_px,
            'now_pct': now_pct,
            'is_today': selected_date == timezone.now().date(),
        }
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
        submitted = False
        form = ExistClientForm()
        khach = None
        if "full_name" in request.GET and "phone" in request.GET:
            submitted = True
            name = str(request.GET.get("full_name")).upper().strip()
            phone = request.GET.get('phone')
            khach = Khach.objects.filter(full_name=name, phone=phone)
        cont = {'formDatHen': form, 'khach': khach, 'submitted': submitted}
        return render(request, self.template, cont)
    
class ExistPickTech(View):
    template = 'datHen/exist_pick_tech.html'
    
    def get(self, request, pk):
        tech = Technician.objects.filter(is_accept_booking=True).exclude(name="anyOne")
        _annotate_tech_off_notices(tech)
        cont = {'allTech': tech}
        request.session['client_id'] = pk
        return render(request, self.template, cont)
    
class ExistSecond(View):
    template = 'datHen/exist_second.html'
    def get(self, request, pk):
        day_comes = request.GET.get('day_comes')
        if day_comes:
            request.session['date'] = day_comes
        get_object_or_404(Technician, id=pk)
        request.session['tech_id'] = pk
        secondForm = DateForm()
        cont = {
                'secondForm': secondForm,
            }
        return render(request, self.template, cont)

class ChoiceServicesExistView(View):
    template = 'datHen/services_choice_exist.html'

    def get(self, request):
        day_comes = request.GET.get('day_comes')
        if day_comes:
            request.session['date'] = day_comes
        if not request.session.get('client_id') or not request.session.get('tech_id') or not request.session.get('date'):
            return _booking_restart(
                request,
                "Please pick a client, technician, and date before choosing services.",
            )
        serviceForm = ServicesChoiceForm(request.GET)
        cont = {
            'form': serviceForm
        }
        return render(request, self.template, cont)
    
    
class ExistThirdStep(View):
    template = 'datHen/exist_third_step.html'

    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy('datHen:listHen')
        return reverse_lazy('ledger:index')

    def _load_booking_state(self, request):
        client_id = request.session.get('client_id')
        tech_id = request.session.get('tech_id')
        booking_date = _parse_booking_date(request.session.get('date'))
        if not client_id or not tech_id or not booking_date:
            return None
        services = _get_selected_services(request)
        if not services.exists():
            return None
        tech = get_object_or_404(Technician, id=tech_id)
        client = get_object_or_404(Khach, id=client_id)
        request.session['service_ids'] = list(services.values_list('id', flat=True))
        return {
            'tech': tech,
            'client': client,
            'booking_date': booking_date,
            'services': services,
            'available': _available_times(tech, booking_date, services),
        }

    def get(self, request):
        state = self._load_booking_state(request)
        if not state:
            return _booking_restart(
                request,
                "Your booking session expired or is missing information. Please start again.",
            )
        form = ThirdFormExist(instance=state['client'])
        form.initial['technician'] = state['tech'].pk
        context = _third_step_context(state)
        context['form'] = form
        return render(request, self.template, context)

    def post(self, request):
        state = self._load_booking_state(request)
        if not state:
            return _booking_restart(
                request,
                "Your booking session expired or is missing information. Please start again.",
            )
        form = ThirdFormExist(request.POST, instance=state['client'])
        if not form.is_valid():
            context = _third_step_context(state)
            context['form'] = form
            return render(request, self.template, context)
        if not state['available']:
            context = _third_step_context(state)
            context['form'] = form
            return render(request, self.template, context)
        khac = form.save(commit=False)
        khac.day_comes = state['booking_date']
        khac.technician = state['tech']
        khac.points = sum(service.price for service in state['services'])
        khac.save()
        khac.services.set(state['services'])
        visit_status = (
            KhachVisit.Status.anyone
            if khac.status == Khach.Status.anyone
            else KhachVisit.Status.online
        )
        utils.saveKhachVisit(
            khac, state['booking_date'], khac.time_at, state['services'], state['tech'], visit_status
        )
        if khac.email:
            utils.sendEmailConfirmation(request, khac)
            messages.success(request, f"{khac.full_name} was scheduled successfully!")
        else:
            messages.info(request, "Appointment booked, but no email provided for confirmation.")
        return redirect(self.get_success_url())


class FirstStep(View):
    template = 'datHen/first_step.html'
    #need to filter user
    def get(self,request):
        tech = Technician.objects.filter(is_accept_booking=True).exclude(name="anyOne")
        _annotate_tech_off_notices(tech)
        cont = {'allTech': tech}
        return render(request, self.template, cont)


class Second(View):
    template = 'datHen/second.html'
    def get(self, request, pk):
        day_comes = request.GET.get('day_comes')
        if day_comes:
            request.session['date'] = day_comes
        request.session['id'] = pk
        secondForm = DateForm()
        cont = {
                'secondForm': secondForm,
            }
        return render(request, self.template, cont)


class ChoiceServicesView(View):
    template = 'datHen/services_choice.html'

    def get(self, request):
        day_comes = request.GET.get('day_comes')
        if day_comes:
            request.session['date'] = day_comes
        if not request.session.get('id') or not request.session.get('date'):
            return _booking_restart(
                request,
                "Please pick a technician and date before choosing services.",
            )
        serviceForm = ServicesChoiceForm(request.GET)
        cont = {
            'form': serviceForm
        }
        return render(request, self.template, cont)


class ThirdStep(View):
    template = 'datHen/third_step.html'

    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy('datHen:listHen')
        return reverse_lazy('ledger:index')

    def _load_booking_state(self, request):
        tech_id = request.session.get('id')
        booking_date = _parse_booking_date(request.session.get('date'))
        if not tech_id or not booking_date:
            return None
        services = _get_selected_services(request)
        if not services.exists():
            return None
        tech = get_object_or_404(Technician, id=tech_id)
        request.session['service_ids'] = list(services.values_list('id', flat=True))
        return {
            'tech': tech,
            'booking_date': booking_date,
            'services': services,
            'available': _available_times(tech, booking_date, services),
        }

    def get(self, request):
        state = self._load_booking_state(request)
        if not state:
            return _booking_restart(
                request,
                "Your booking session expired or is missing information. Please start again.",
            )
        form = ThirdForm(initial={'technician': state['tech'].pk})
        context = _third_step_context(state)
        context['form'] = form
        return render(request, self.template, context)

    def post(self, request):
        state = self._load_booking_state(request)
        if not state:
            return _booking_restart(
                request,
                "Your booking session expired or is missing information. Please start again.",
            )
        form = ThirdForm(request.POST)
        if not form.is_valid():
            context = _third_step_context(state)
            context['form'] = form
            return render(request, self.template, context)
        if not state['available']:
            context = _third_step_context(state)
            context['form'] = form
            return render(request, self.template, context)
        total_point = sum(service.price for service in state['services'])
        existing_client = form.cleaned_data.get('existing_client')
        if existing_client:
            khac = existing_client
            khac.day_comes = state['booking_date']
            khac.technician = state['tech']
            khac.time_at = form.cleaned_data['time_at']
            khac.status = form.cleaned_data['status']
            khac.points = total_point
            khac.email = form.cleaned_data['email']
            khac.save()
        else:
            khac, _ = Khach.objects.get_or_create(
                full_name=form.cleaned_data['full_name'],
                phone=form.cleaned_data['phone'],
                defaults={
                    'day_comes': state['booking_date'],
                    'technician': state['tech'],
                    'time_at': form.cleaned_data['time_at'],
                    'status': form.cleaned_data['status'],
                    'email': form.cleaned_data['email'],
                    'points': total_point,
                },
            )
            if khac.day_comes != state['booking_date'] or khac.technician_id != state['tech'].pk:
                khac.day_comes = state['booking_date']
                khac.technician = state['tech']
                khac.time_at = form.cleaned_data['time_at']
                khac.status = form.cleaned_data['status']
                khac.email = form.cleaned_data['email']
                khac.points = total_point
                khac.save()
        khac.services.set(state['services'])
        visit_status = (
            KhachVisit.Status.anyone
            if khac.status == Khach.Status.anyone
            else KhachVisit.Status.online
        )
        utils.saveKhachVisit(
            khac, state['booking_date'], khac.time_at, state['services'], state['tech'], visit_status
        )
        if khac.email:
            utils.sendEmailConfirmation(request, khac)
            messages.success(request, f"{khac.full_name} was scheduled successfully!")
        else:
            messages.info(request, "Appointment booked, but no email provided for confirmation.")
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
        # send email to client here before clearing services
        client.services.clear()
        client.status = Khach.Status.cancel
        client.save()
        utils.sendEmailCanceled(client=client)
        utils.cancelKhachVisit(client=client)
        messages.success(request, "Your services have been canceled successfully.")
        return redirect(self.get_success_url())
    
class CancelKhachVisit(LoginRequiredMixin, DeleteView):
    model = KhachVisit
    template_name = "datHen/user_delete_khachvisit.html"
    success_url = reverse_lazy('datHen:listHen')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['visit'] = self.object
        return context
    
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
        context['today'] = timezone.now().today().date()
        return context
        
    def get_success_url(self):
        return self.success_url

class VisitDetailView(LoginRequiredMixin, UpdateView):
    model = KhachVisit
    template_name = 'datHen/visit_detail.html'
    success_url = reverse_lazy('datHen:listHen')
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['visit'] = self.object
        return context

def schedule_get_client(request):
    phone = request.GET.get('phone')
    client_list = Khach.objects.filter(phone=phone)
    data = [{'full_name': client.full_name, 'phone': str(client.phone)} for client in client_list]
    return JsonResponse(data, safe=False)
    
class ScheduleViewUser(LoginRequiredMixin, View):
    template = "datHen/schedule_user.html"
    success_url = reverse_lazy('datHen:listHen')
    def get(self,request):
        form = DatHenForm()
        context = {
            'form': form
        }
        return render(request, self.template, context)
    def post(self, request):
        form = DatHenForm(request.POST)
        if not form.is_valid():
            context = {
                'form': form
            }
            return render(request, self.template, context)
        full_name = form.cleaned_data['full_name'].upper().strip()
        phone = form.cleaned_data['phone']
        services = form.cleaned_data['services']
        tech = form.cleaned_data['technician']
        day_comes = form.cleaned_data['day_comes']
        time_at = form.cleaned_data['time_at']
        status = form.cleaned_data['status']
        total_point = sum([service.price for service in services])
        existing_client = form.cleaned_data.get('existing_client')
        
        if existing_client:
            client = existing_client
            client.day_comes = day_comes
            client.technician = tech
            client.time_at = time_at
            client.status = status
            client.save()
            
        else:
            client, _ = Khach.objects.get_or_create(full_name=full_name, phone=phone,
                                                    defaults={'day_comes': day_comes, 'technician': tech,
                                                              'time_at': time_at,
                                                              'status': status})
        client.services.set(services)
        client.points = total_point
        client.save()
        form.instance = client
        visit_status = (
            KhachVisit.Status.anyone
            if status == Khach.Status.anyone
            else KhachVisit.Status.phone
        )
        utils.saveKhachVisit(client, day_comes, time_at, services, tech, visit_status)
        messages.success(request, f"{form.instance.full_name} was scheduled successfully!")
        return redirect(self.success_url)

