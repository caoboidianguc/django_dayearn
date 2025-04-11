
from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
import datetime
from datetime import timedelta
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _


class Technician(models.Model):
    name = models.CharField(max_length=25)
    phone = PhoneNumberField()
    email = models.EmailField(max_length=40, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    start_work_at = models.TimeField()
    end_work = models.TimeField()
    isWork = models.BooleanField(default=False)
    picture = models.ImageField(upload_to='tech_pictures/', null=True, editable=True)
    services = models.ManyToManyField("Service", blank=True, related_name="tech")
    time_come_in = models.DateTimeField(null=True)
    work_days = models.CharField(max_length=7, default="1111110", help_text="MTWTFSS: 1 for work, 0 for off")
    vacation_start = models.DateField(null=True, blank=True, help_text="Start vacation")
    vacation_end = models.DateField(null=True, blank=True, help_text="End vacation, back work!")
    date_go_work = models.DateField(null=True, blank=True)
    history = HistoricalRecords()
    
    def is_on_vacation(self, check_date):
        if self.vacation_start and self.vacation_end:
            return self.vacation_start <= check_date <= self.vacation_end
        return False
    def still_vacation(self):
        if self.vacation_end:
            return self.vacation_end > timezone.now().date()
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
        # now = datetime.datetime.now()
        allClients = self.khachs.all() #filter(day_comes__gte=now)
        return allClients
    
    def get_today_clients(self):
        hnay = self.get_khachVisit().filter(day_comes=datetime.date.today()) #.exclude(status=Khach.Status.cancel)
        return hnay.order_by('time_at')
    
    def get_khachVisit(self):
        return self.khachvisits.all()
                
    def get_available_with(self, ngay, thoigian):
        start = datetime.datetime(1970,1,1, hour=self.start_work_at.hour, minute=self.start_work_at.minute)
        end = datetime.datetime(1970,1,1, hour=self.end_work.hour, minute=self.end_work.minute)
        clients = self.get_khachVisit().filter(day_comes=ngay)
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
    
    def get_services_today(self):
        now = datetime.datetime.now()
        clients = self.get_today_clients().filter(time_at__lte=now)
        all_ser = []
        for client in clients:
            all_ser.extend(client.get_services())
        return len(all_ser)
    
    # def get_available_with(self, ngay, thoigian):
    #     day_of_week = ngay.weekday()
    #     try:
    #         work_day = TechWorkDay.objects.get(tech=self, day_of_week=day_of_week)
    #         start = datetime.datetime.combine(ngay, work_day.start_time)
    #         end = datetime.datetime.combine(ngay, work_day.end_time)
    #     except TechWorkDay.DoesNotExist:
    #         return
    #     clients = self.get_clients().filter(day_comes=ngay)
    #     time_cal = start
    #     while time_cal < end:
    #         time_compare = time_cal + datetime.timedelta(minutes=thoigian)
    #         overlap = False
            
    #         for client in clients:
    #             client_start = datetime.datetime.combine(ngay, client.start_at())
    #             client_end = datetime.datetime.combine(ngay, client.get_done_at())
                
    #             if (client_start <= time_cal < client_end) or (time_cal < client_start < time_compare):
    #                 overlap = True
    #                 break
            
    #         if not overlap:
    #             yield time_cal.time()
    #         time_cal += datetime.timedelta(minutes=15)

Day_Of_Week = (
    (0, _('Monday')),
    (1, _('Tuesday')),
    (2, _('Wednesday')),
    (3, _('Thursday')),
    (4, _('Friday')),
    (5, _('Saturday')),
    (6, _('Sunday')),
)

class TechWorkDay(models.Model):
    tech = models.ForeignKey(Technician, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    day_of_week = models.IntegerField(choices=Day_Of_Week)

class Khach(models.Model):
    class Status(models.TextChoices):
        online = "Confirmed"
        anyone = "Anyone"
        cancel = "Cancel"
    full_name = models.CharField(max_length=25, validators=[MinLengthValidator(5)])
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
    tag = models.CharField(max_length=20, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    history = HistoricalRecords()
    
    class Meta:
        unique_together = ('full_name','phone',)#put email here for production, increase secure for chat
        ordering = ['full_name','-day_comes']

    def __str__(self) -> str:
        return self.full_name
    
    def phone_formatted(self):
        so = str(self.phone)
        if len(so) == 12:
            so = f"{so[:2]} ({so[2:5]}) {so[5:8]}-{so[8:]}"
            return so
        else:
            return so
    def future_visit(self):
        return self.khachvisits.filter(day_comes__gte=datetime.date.today()).exists()
        
    def can_post_chat(self):
        return self.khachvisits.filter(day_comes__lt=datetime.date.today()).exists()
        
    def get_chat_url(self):
        return reverse("ledger:chat_room", kwargs={'pk':self.pk})
    
    def get_cancel_url(self):
        return reverse("datHen:cancel_confirm", kwargs={'pk':self.pk})
    
    def get_client_detail_url(self):
        return reverse("datHen:client_detail", kwargs={'pk':self.pk})
    
    def get_absolute_url(self):
        return reverse("datHen:exist_found", kwargs={"pk": self.pk})
    
    def unique_error_message(self, model_class, unique_check):
        #override message __all__
        if unique_check == ("full_name", "phone"):
            return "A client with this Full name and Phone already exists."
        return super().unique_error_message(model_class, unique_check)
    
    def get_all_chat(self):
        return self.client_chats.all()
    def get_all_like(self):
        return self.liked_chats.all()
    
class KhachVisit(models.Model):
    class Status(models.TextChoices):
        online = "Confirmed"
        anyone = "Anyone"
        cancel = "Cancel"
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name="khachvisits", null=True)
    client = models.ForeignKey(Khach, on_delete=models.CASCADE, related_name="khachvisits")
    services = models.ManyToManyField("Service", blank=True)
    status = models.CharField(choices=Status.choices, max_length=20, default=Status.online, help_text="Choose anyone as an alternate!")
    day_comes = models.DateField()
    time_at = models.TimeField()
    total_spent = models.DecimalField(max_digits=7, decimal_places=2, editable=False, null=True)
    def __str__(self) -> str:
        return self.client.full_name
    
    def get_visit_detail_url(self):
        return reverse("datHen:visit_detail", kwargs={'pk':self.pk})
    
    def get_cancel_url(self):
        return reverse("datHen:cancel_khachvisit", kwargs={'pk':self.pk})
    
    def get_time_done(sefl):
        tong = 0
        for service in sefl.services.all():
            tong += service.time_perform.total_seconds()
        if tong > 0:
            tong = tong/60
            return tong
        return tong
    
    def get_services(self):
        services = []
        for dv in self.services.all():
            services.append(dv)
        return services
    
    def get_done_at(self):
        gio = datetime.datetime(1970,1,1,hour=self.time_at.hour, minute=self.time_at.minute) + timedelta(minutes=self.get_time_done())
        return datetime.time(hour=gio.hour, minute=gio.minute)
    def start_at(self):
        them = datetime.datetime(1970,1,1, hour=self.time_at.hour, minute=self.time_at.minute)
        return datetime.time(hour=them.hour, minute=them.minute)
   
class Service(models.Model):
    class Category(models.TextChoices):
        nail = "Nail Enhancement"
        mani = "Manicure"
        pedi = "Pedicure"
        wax = "Wax"
        fix = "Fix"
    service = models.CharField(max_length=30)
    price = models.FloatField()
    time_perform = models.DurationField(default=timezone.timedelta(minutes=45))
    description = models.CharField(max_length=800, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(choices=Category.choices, max_length=20, default=Category.nail, help_text="Choose one of the categories.")


    def __str__(self) -> str:
        return self.service
    def save(self, *kwag, **kwargs):
        if self.time_perform <= timedelta(0):
            raise ValidationError("Time must be greater than  0 !")
        return super().save(*kwag, **kwargs)
    class Meta:
        unique_together = ('service','price')
        ordering = ['price']
    def get_url(self):
        return reverse("ledger:service_detail", kwargs={'pk':self.pk})
    def time_in_minute(self):
        return self.time_perform.total_seconds()/60
        

class Chat(models.Model):
    isNew = models.BooleanField(default=True)
    text = models.TextField(validators=[MinLengthValidator(1, "What's your message.")])
    created_at = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chats", null=True)
    client = models.ForeignKey(Khach, on_delete=models.CASCADE, related_name="client_chats", null=True, blank=True)
    def __str__(self):
        if len(self.text) < 200 : return self.text
        return self.text[:200] + ' ...'

    @property
    def nickName(self):
        if self.client:
            nickname = self.client.full_name[:3]
            return nickname
        return "@Manager"
    @property
    def total_likes(self):
        return self.likes.count()
    
    @property
    def client_name(self):
        return self.client.full_name if self.client else "@Manager"
    
    @property
    def get_reply_count(self):
        return self.replies.count()
    
    def get_detail_url(self):
        return reverse('ledger:user_chat_detail', kwargs={'pk': self.pk})

 
class Like(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="likes")
    client = models.ForeignKey(Khach, on_delete=models.CASCADE, related_name="liked_chats", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owner_likes", null=True)
    class Meta:
        unique_together = [('chat', 'client'), ('chat','owner'),]
        
    def __str__(self):
        if self.client:
            return f"{self.client} liked chat {self.chat.id}"
        return f"{self.owner} liked chat {self.chat.id}"
    
class Supply(models.Model):
    title = models.CharField(max_length=42, validators=[MinLengthValidator(2)])
    quantity = models.PositiveIntegerField(default=1)
    info = models.CharField(max_length=250, null=True)
    price = models.FloatField(max_length=10, null=True)
    is_wanted = models.BooleanField(default=True)
    date = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="supplies")
    class Meta:
        unique_together = ('title',)
    def __str__(self):
        return self.title
