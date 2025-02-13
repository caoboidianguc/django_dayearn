from typing import Any
from django import forms
from datetime import timedelta, date
from ledger.models import Khach, Service, Technician
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
    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            choice for choice in self.fields['status'].choices if choice[0] != Khach.Status.cancel
        ]
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

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        return full_name.upper() if full_name else ''
    
    class Meta:
        model = Khach
        fields = ['technician', 'services', 'full_name', 'phone', 'email', 'day_comes', 'time_at', 'status']
        
class UserExistClientForm(forms.ModelForm):
    class Meta:
        model = Khach
        fields = ['phone']

class ExistClientForm(forms.ModelForm):
    class Meta:
        model = Khach
        fields = ['full_name','phone']
        


class DateForm(forms.ModelForm):
    def clean_day_comes(self):
        date = super().clean()
        date = self.cleaned_data["day_comes"]
        if date.weekday() == 6:
            raise ValidationError("Sunday is walkin")
        return date
    class Meta:
        model=Khach
        fields = ['day_comes']

    day_comes = forms.DateField(
        widget=ChonNgay(attrs={'min': date.today()}),
        label="Please Pick a day"
        )
    
     
  
class ThirdForm(forms.ModelForm):
    
    class Meta:
        model=Khach
        fields = ['time_at','full_name', 'phone', 'email', 'status','technician']
    technician = forms.widgets.HiddenInput()
    
    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            choice for choice in self.fields['status'].choices if choice[0] != Khach.Status.cancel
        ]
        
    email = forms.CharField(
        label="",
        required=False,
        widget=forms.widgets.EmailInput(attrs={'placeholder':'For booking confirmations'}))
    
    phone = PhoneNumberField(widget=forms.TextInput(
                        attrs={'placeholder': 'Phone Number'}),
                        label="")
    
    
    full_name = forms.CharField(
        label="",
        min_length = 2,
        widget=forms.TextInput(
        attrs={
            'placeholder': 'Full Name'
        }
    ))
    
    def clean_full_name(self):
        data = super().clean()
        data = self.cleaned_data['full_name']
        return str(data).upper().strip()



class ThirdFormExist(forms.ModelForm):
    class Meta:
        model=Khach
        fields = ['time_at', 'email', 'status','technician']
    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            choice for choice in self.fields['status'].choices if choice[0] != Khach.Status.cancel
        ]
    technician = forms.widgets.HiddenInput()
     
    email = forms.CharField(
        label="",
        required=False,
        widget=forms.widgets.EmailInput(attrs={'placeholder':'For booking confirmations'}))
    
    def clean_full_name(self):
        data = super().clean()
        data = self.cleaned_data['full_name']
        return str(data).upper()
    

class ServicesChoiceForm(forms.Form):
    dichvu = forms.ModelMultipleChoiceField(queryset=Service.objects.all(), 
                                              widget=forms.CheckboxSelectMultiple,
                                              label = "Choose Services:")
    
    