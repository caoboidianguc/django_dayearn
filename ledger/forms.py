from django import forms
from .models import Technician, Khach, Service, Chat, TechWorkDay, Supply, Complimentary, Day_Of_Week
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.formfields import PhoneNumberField
from datHen.forms import ChonNgay
from django.utils import timezone

service_queryset = Service.objects.exclude(service="tax")

class ComplimentaryForm(forms.ModelForm):
    class Meta:
        model = Complimentary
        fields = ['title', 'description','photo',"category"]
    photo = forms.ImageField(
        widget=forms.FileInput(),
        label="Upload Picture",
        required=False
    )
    
class TechForm(forms.ModelForm):
    phone = PhoneNumberField(widget=forms.TextInput(
                        attrs={'placeholder': 'Phone Number'}),
                        label="")
    name = forms.CharField(widget=forms.TextInput(
                        attrs={'placeholder': 'Tech Name'}),
                        label="")
    start_work_at = forms.TimeField(widget=forms.TimeInput(attrs={'type':'time'}))
    end_work = forms.TimeField(
        widget=ChonNgay(attrs={
            'type': 'time'
            }))
    email = forms.CharField(widget=forms.TextInput(
                        attrs={'placeholder': 'Email'}),
                        label="",
                        required=False)
    class Meta:
        model = Technician
        fields = ["name","phone", "email","start_work_at","end_work","experience","bio","picture"]
    picture = forms.ImageField(
        widget=forms.FileInput(),
        label="Upload Picture",
        required=False
    )

class TechWorkDayForm(forms.ModelForm):
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Specific date (optional)",
        help_text="Leave blank for every-week schedule (e.g. every Tuesday off until you turn back on). Pick a date for a one-time change only.",
    )
    day_of_week = forms.ChoiceField(
        choices=[('', 'Pick a day')] + list(Day_Of_Week),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Day of week",
        help_text="Pick the weekday for a regular every-week schedule. Stays on or off until you change it.",
    )
    is_working = forms.TypedChoiceField(
        choices=[('true', 'On'), ('false', 'Off')],
        required=False,
        initial='true',
        label="Working this day",
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = TechWorkDay
        fields = ['date', 'day_of_week', 'is_working', 'start_time', 'end_time']

    start_time = forms.TimeField(
        required=False,
        input_formats=["%H:%M"],
        widget=ChonNgay(attrs={"type": "time", "class": "form-control"}),
    )
    end_time = forms.TimeField(
        required=False,
        input_formats=["%H:%M"],
        widget=ChonNgay(attrs={"type": "time", "class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        day_of_week = cleaned_data.get('day_of_week')
        is_working = cleaned_data.get('is_working', 'true') == 'true'
        cleaned_data['is_working'] = is_working
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if date:
            cleaned_data['day_of_week'] = date.weekday()
        elif day_of_week not in (None, ''):
            cleaned_data['day_of_week'] = int(day_of_week)
        else:
            raise forms.ValidationError("Pick a day of the week, or choose a specific date.")

        if is_working:
            if start_time and end_time and start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time.")
        else:
            cleaned_data['start_time'] = None
            cleaned_data['end_time'] = None

        return cleaned_data
        
class ClientForm(forms.ModelForm):
    email = forms.CharField(required=False)
    class Meta:
        model = Khach
        fields = ['full_name', 'phone', 'email', 'services']
        

    
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['service','price','time_perform','description','category']
    time_perform = forms.IntegerField(
        label="Time Perform (minutes)",
        min_value=10,
        help_text="Enter the time in minutes."
    )
    description = forms.CharField(widget=forms.Textarea(
                        attrs={'placeholder': 'You can add later',
                               'rows': 4,
                               'cols': 50}),
                        label="Enter description of the service.",
                        required=False,
                        )
    def clean_time_perform(self):
        phut = self.cleaned_data['time_perform']
        return timezone.timedelta(minutes=phut)


class TaiKhoanCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)
        
    
class VacationForm(forms.ModelForm):
    vacation_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Last day off (optional)",
        help_text="Leave blank to stay off until you turn back on.",
    )

    class Meta:
        model = Technician
        fields = ['vacation_start', 'vacation_end']
        widgets = {
            'vacation_start': forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
        help_texts = {
            'vacation_start': 'First day off for consecutive days away.',
        }
        
class ChatForm(forms.ModelForm):
    text = forms.CharField(required=True,min_length=1, max_length=500, strip=True, label="",
                           widget=forms.TextInput(
                        attrs={'placeholder': 'i gonna say it'}))
    class Meta:
        model = Chat
        fields = ['text']
        
class KhachWalkin(forms.ModelForm):
    class Meta:
        model = Khach
        fields = ['full_name', 'phone','services']
    def clean(self):
        clean_data = super().clean()
        full_name = clean_data.get('full_name')
        phone = clean_data.get('phone')
        if full_name and phone:
            existing_client = Khach.objects.filter(full_name=full_name.upper(), phone=phone).first()
            if existing_client:
                clean_data['existing_client'] = existing_client
            else:
                clean_data['existing_client'] = None
        return clean_data
    def validate_unique(self):
        if self.cleaned_data.get('existing_client'):
            return
        return super().validate_unique()

    services = forms.ModelMultipleChoiceField(queryset=service_queryset, widget=forms.CheckboxSelectMultiple(),
                                              label='How can we help you today:',
                                              required=True,
                                              error_messages={'required':'Please choose at least one service.'},)


class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ['title','quantity','info']
    info = forms.CharField(widget=forms.Textarea(attrs={'placeholder':'Detail for item'}),
                           required=False)
    
class ContactForm(forms.Form):
    name = forms.CharField(min_length=3,max_length=25, strip=True)
    email = forms.EmailField()
    phone = PhoneNumberField(required=True)
    message = forms.CharField(min_length=10, max_length=350,widget=forms.Textarea(
                        attrs={'placeholder': 'Message',
                               'rows': 4,
                               'cols': 50}),)
    
    