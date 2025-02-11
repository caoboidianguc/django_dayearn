from collections.abc import MutableMapping
from typing import Any
from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
import datetime
from datetime import timedelta
from taggit.managers import TaggableManager



class Technician(models.Model):
    name = models.CharField(max_length=25)
    phone = PhoneNumberField()
    email = models.EmailField(max_length=40, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    start_work_at = models.TimeField()
    end_work = models.TimeField()
    isWork = models.BooleanField(default=False)
    picture = models.ImageField(upload_to='tech_pictures/', null=True, editable=True)
    content_type = models.CharField(max_length=256, null=True, help_text='The MIMEType of the file')
    services = models.ManyToManyField("Service", blank=True, related_name="tech")
    time_come_in = models.TimeField(null=True)
    work_days = models.CharField(max_length=7, default="1111110", help_text="MTWTFSS: 1 for work, 0 for off")
    vacation_start = models.DateField(null=True, blank=True, help_text="Start vacation")
    vacation_end = models.DateField(null=True, blank=True, help_text="End vacation, back work!")
    date_go_work = models.DateField(null=True, blank=True)
    def is_on_vacation(self, check_date):
        if self.vacation_start and self.vacation_end:
            return self.vacation_start <= check_date <= self.vacation_end
        return False
    
    class Meta:
        unique_together = ('name','phone',)
        ordering = ['name']
    def clean(self):
        if self.start_work_at > self.end_work:
            raise ValidationError("Start time must be before end time")
    def get_absolute_url(self):
        return reverse("datHen:technician_detail", kwargs={"pk": self.pk})
    
    def __str__(self) -> str:
        return self.name
        
        
    def get_clients(self):
        allClients = self.khachs.all()
        return allClients
    
    def get_today_clients(self):
        return self.get_clients().filter(day_comes=datetime.date.today()).order_by('time_at')
    
    
    def get_available(self, ngay):
        start = datetime.datetime(1970,1,1, hour=self.start_work_at.hour, minute=self.start_work_at.minute)
        end = datetime.datetime(1970,1,1, hour=self.end_work.hour, minute=self.end_work.minute)
        clients = self.get_clients().filter(day_comes=ngay)
        xongs = [client for client in clients]
        thoigian = start
        while thoigian < end:
            if clients:
                if not any(khach.start_at() <= thoigian.time() < khach.get_done_at() for khach in xongs):
                    yield thoigian
                thoigian += timedelta(minutes=15)
            else:
                yield thoigian
                thoigian += timedelta(minutes=15)
                
    def get_available_with(self, ngay, thoigian):
        start = datetime.datetime(1970,1,1, hour=self.start_work_at.hour, minute=self.start_work_at.minute)
        end = datetime.datetime(1970,1,1, hour=self.end_work.hour, minute=self.end_work.minute)
        clients = self.get_clients().filter(day_comes=ngay)
        xongs = [client for client in clients]
        timeCal = start
        
        while timeCal < end:
            if not clients:
                yield timeCal
                timeCal += timedelta(minutes=15)
            else:
                timeCompare = timeCal + timedelta(minutes=thoigian)
                over_lap = False
                for khach in xongs:
                    if khach.start_at() <= timeCal.time() < khach.get_done_at() or timeCal.time() < khach.start_at() <= timeCompare.time():
                        over_lap = True
                        break
                if not over_lap:
                    yield timeCal
                timeCal += timedelta(minutes=15)

    @property
    def timeSpan(self):
        batdau = datetime.datetime(1970,1,1, hour=self.start_work_at.hour, minute=self.start_work_at.minute)
        ketthuc = datetime.datetime(1970,1,1, hour=self.end_work.hour, minute=self.end_work.minute)
        while batdau < ketthuc:
            yield batdau
            batdau += timedelta(minutes=15)
    
    def get_services_of_tech(self):
        clients = self.get_today_clients()
        all_ser = []
        for client in clients:
            all_ser += client.get_services()
        return all_ser
    
   
        
    
    
class Khach(models.Model):
    class Status(models.TextChoices):
        online = "Confirmed"
        anyone = "Anyone"
        cancel = "Cancel"
    full_name = models.CharField(max_length=25)
    phone = PhoneNumberField()
    email = models.EmailField(max_length=40, null=True, blank=True, help_text="Enter your email for booking confirmations.")
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True, related_name='khachs')
    points = models.PositiveIntegerField(default=0)
    first_comes = models.DateTimeField(editable=False,auto_now_add=True)
    desc = models.TextField(max_length=250,blank=True, null=True)
    services = models.ManyToManyField("Service", blank=True, related_name="khachs")
    status = models.CharField(choices=Status.choices, max_length=20, default=Status.online, help_text="Choose anyone as an alternate!")
    day_comes = models.DateField()
    time_at = models.TimeField()
    tags = TaggableManager()
    birthday = models.DateField(null=True, blank=True)
    
    
    class Meta:
        unique_together = ('full_name','phone',)
        ordering = ['full_name','-day_comes']

    def __str__(self) -> str:
        return self.full_name
    # this should be on clean method
    def huy(self):
        if self.status == "Cancel":
            self.time_at = self.technician.end_work
            return self.time_at
     
    def get_services(self):
        services = []
        for dv in self.services.all():
            services.append(dv)
        return services
    
    def get_time_done(sefl):
        tong = 0
        for service in sefl.services.all():
            tong += service.time_perform.total_seconds()
        if tong > 0:
            tong = tong/60
            return tong
        return tong
    
    def get_done_at(self):
        gio = datetime.datetime(1970,1,1,hour=self.time_at.hour, minute=self.time_at.minute) + timedelta(minutes=self.get_time_done())
        return datetime.time(hour=gio.hour, minute=gio.minute)
    def start_at(self):
        them = datetime.datetime(1970,1,1, hour=self.time_at.hour, minute=self.time_at.minute)
        return datetime.time(hour=them.hour, minute=them.minute)
    
    def get_chat_url(self):
        return reverse("ledger:chat_room", kwargs={'pk':self.pk})
    
    def get_cancel_url(self):
        return reverse("datHen:cancel_confirm", kwargs={'pk':self.pk})
    
    def get_absolute_url(self):
        return reverse("datHen:exist_found", kwargs={"pk": self.pk})
    def unique_error_message(self, model_class, unique_check):
        #override message __all__
        if unique_check == ("full_name", "phone"):
            return "A client with this Full name and Phone already exists."
        return super().unique_error_message(model_class, unique_check)
    

    
    
class Service(models.Model):
    service = models.CharField(max_length=30)
    price = models.FloatField()
    time_perform = models.DurationField(default=timezone.timedelta(minutes=45))
    description = models.CharField(max_length=300, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.service
    def save(self, *kwag, **kwargs):
        if self.time_perform <= timedelta(0):
            raise ValidationError("Time must be greater than  0 !")
        return super().save(*kwag, **kwargs)
    class Meta:
        unique_together = ('service','price')
        ordering = ['price']
        
    def time_in_minute(self):
        return self.time_perform.total_seconds()/60
        

class Chat(models.Model):
    text = models.TextField(validators=[MinLengthValidator(1, "What's your message.")])
    created_at = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chats", null=True)
    client = models.ForeignKey(Khach, on_delete=models.DO_NOTHING, related_name="client_chats", null=True, blank=True)
    def __str__(self):
        if len(self.text) < 45 : return self.text
        return self.text[:40] + ' ...'
    
    @property
    def client_name(self):
        return self.client.full_name if self.client else "@Manager"
    
