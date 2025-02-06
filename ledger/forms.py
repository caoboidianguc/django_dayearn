from django import forms
from .models import Technician, Khach, Service, Chat
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.formfields import PhoneNumberField
from datHen.forms import ChonNgay
from django.utils import timezone



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
        fields = ["name","phone", "email","start_work_at","end_work","picture"]
    picture = forms.ImageField(
        widget=forms.FileInput(),
        label="Upload Picture",
        required=False
    )
        
        
class ClientForm(forms.ModelForm):
    email = forms.CharField(required=False)
    class Meta:
        """Meta definition for Clientform."""
        model = Khach
        fields = ['full_name', 'phone', 'email', 'services']
        

    
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['service','price','time_perform']
    time_perform = forms.IntegerField(
        label="Time Perform (minutes)",
        min_value=10,
        help_text="Enter the time in minutes."
    )
    def clean_time_perform(self):
        phut = self.cleaned_data['time_perform']
        return timezone.timedelta(minutes=phut)


class TaiKhoanCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)
        
    
class VacationForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ['vacation_start','vacation_end']
        widgets = {
            'vacation_start': forms.DateInput(attrs={"type":"date"}),
            'vacation_end': forms.DateInput(attrs={"type":"date"}),
        }
        
class ChatForm(forms.ModelForm):
    text = forms.CharField(required=True,min_length=5, max_length=500, strip=True)
    class Meta:
        model = Chat
        fields = ['text']