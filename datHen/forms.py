from typing import Any
from django import forms
from datetime import timedelta, date
import datetime
from ledger.models import Khach, Service
from phonenumber_field.formfields import PhoneNumberField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column
from django.core.exceptions import ValidationError

 

    
class ChonNgay(forms.widgets.DateInput):
    input_type = 'date'
    input_formats= "%Y-%m-%d"
    
#date format is yyyy-mm-dd
# time is 24h
class DatHenFrom(forms.ModelForm):
    
    day_comes = forms.DateField(
        widget=ChonNgay(attrs={'min': date.today()})
        )
  
    time_at = forms.TimeField(
        input_formats=["%H:%M"],
        widget=ChonNgay(attrs={
            "type":"time",
            })
        )    
    email = forms.CharField(
        label="",
        required=False,
        widget=forms.widgets.EmailInput(attrs={'placeholder':'Email Optional'}))
    
    phone = PhoneNumberField(widget=forms.TextInput(
                        attrs={'placeholder': 'Phone Number'}),
                        label="")
    
    services = forms.ModelMultipleChoiceField(queryset=Service.objects.all() ,widget=forms.CheckboxSelectMultiple())
    
    full_name = forms.CharField(
        label="",
        widget=forms.TextInput(
        attrs={
            'placeholder': 'Full Name'
        }
    ))
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    def clean_full_name(self):
        data = super().clean()
        data = self.cleaned_data['full_name']
        return str(data).upper()
    
    # def clean_time_at(self):
    #     gio_den = super().clean()
    #     gio_den = self.cleaned_data['time_at']
    #     day_comes = super().clean()
    #     day_comes = self.cleaned_data['day_comes']
    #     bamuoi = datetime.datetime.now() + timedelta(minutes=10)
    #     if day_comes == date.today() and gio_den < datetime.time(hour=bamuoi.hour, minute=bamuoi.minute):
    #         raise ValidationError("Please make schedule 30 minutes ahead! \n Or gives a call to check available.")
    #     return gio_den
    class Meta:
        
        model = Khach
        fields = ['technician', 'services', 'full_name', 'phone', 'email', 'day_comes', 'time_at', 'status']
        
  



class ExistClientForm(forms.ModelForm):
    
    class Meta:
        model = Khach
        fields = ['full_name','phone']
        


class SecondStepForm(forms.ModelForm):
    
    class Meta:
        model=Khach
        fields = ['day_comes','technician']
    technician = forms.widgets.HiddenInput()
    day_comes = forms.DateField(
        widget=ChonNgay(attrs={'min': date.today()})
        )
     
  

class ThirdForm(forms.ModelForm):
    
    class Meta:
        model=Khach
        fields = ['services','time_at','full_name', 'phone', 'email', 'status','technician']
    technician = forms.widgets.HiddenInput()
    # time_at = forms.TimeField(
    #     input_formats=["%H:%M"],
    #     widget=ChonNgay(attrs={
    #         "type":"time",
    #         })
    #     )    
    email = forms.CharField(
        label="",
        required=False,
        widget=forms.widgets.EmailInput(attrs={'placeholder':'Email Optional'}))
    
    phone = PhoneNumberField(widget=forms.TextInput(
                        attrs={'placeholder': 'Phone Number'}),
                        label="")
    
    services = forms.ModelMultipleChoiceField(queryset=Service.objects.all() ,widget=forms.CheckboxSelectMultiple())
    
    full_name = forms.CharField(
        label="",
        widget=forms.TextInput(
        attrs={
            'placeholder': 'Full Name'
        }
    ))
    
    def clean_full_name(self):
        data = super().clean()
        data = self.cleaned_data['full_name']
        return str(data).upper()
    # def clean_day_comes(self):
    #     data = self.cleaned_data["day_comes"]
    #     if data < date.today():
    #         raise ValidationError("Your schedule was in the past!")
    #     return data
    


class ThirdFormExist(forms.ModelForm):
    class Meta:
        model=Khach
        fields = ['services','time_at', 'email', 'status','technician']
       
    technician = forms.widgets.HiddenInput()
     
    email = forms.CharField(
        label="",
        required=False,
        widget=forms.widgets.EmailInput(attrs={'placeholder':'Email Optional'}))
    
    
    services = forms.ModelMultipleChoiceField(queryset=Service.objects.all() ,widget=forms.CheckboxSelectMultiple())
        
    def clean_full_name(self):
        data = super().clean()
        data = self.cleaned_data['full_name']
        return str(data).upper()