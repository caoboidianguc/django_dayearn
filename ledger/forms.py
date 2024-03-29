from django import forms
from .models import Technician, Khach, Service, DayOff, TakeTurn
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.formfields import PhoneNumberField
from datHen.forms import ChonNgay



class TechForm(forms.ModelForm):
    phone = PhoneNumberField(widget=forms.TextInput(
                        attrs={'placeholder': 'Phone Number'}),
                        label="")
    name = forms.CharField(widget=forms.TextInput(
                        attrs={'placeholder': 'Tech Name'}),
                        label="")
    # start_work_at = forms.TimeField(
    #     widget=ChonNgay(attrs={
    #         'type': 'time'
    #     }))
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
        fields = ["name","phone", "email","start_work_at","end_work"]
        
        
class TurnForm(forms.ModelForm):
    class Meta:
        model = TakeTurn
        fields = ['tech', 'services']

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


class TaiKhoanCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("email",)
        
    

class DayOffForm(forms.ModelForm):
    
    class Meta:
        model = DayOff
        fields = '__all__'
