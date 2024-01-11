# Generated by Django 5.0.1 on 2024-01-11 13:00

import django.db.models.deletion
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dichVu', models.CharField(max_length=30)),
                ('gia', models.FloatField()),
                ('thoiGian', models.DurationField()),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Technician',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('email', models.EmailField(blank=True, max_length=40, null=True)),
                ('isWork', models.BooleanField(default=False)),
                ('start_work_at', models.TimeField()),
                ('end_work', models.TimeField()),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'phone')},
            },
        ),
        migrations.CreateModel(
            name='DayOff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('note', models.CharField(blank=True, max_length=255, null=True)),
                ('tech', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dayoff', to='ledger.technician')),
            ],
        ),
        migrations.CreateModel(
            name='Khach',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=25)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('email', models.EmailField(blank=True, max_length=40, null=True)),
                ('diem', models.PositiveIntegerField(default=0)),
                ('ngaydau', models.DateTimeField(auto_now_add=True)),
                ('desc', models.TextField(blank=True, max_length=250, null=True)),
                ('status', models.CharField(choices=[('WebSite', 'Online'), ('Cancel', 'Cancel')], default='WebSite', max_length=12)),
                ('day_comes', models.DateField()),
                ('time_at', models.TimeField()),
                ('services', models.ManyToManyField(blank=True, related_name='khachs', to='ledger.service')),
                ('technician', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='khachs', to='ledger.technician')),
            ],
            options={
                'ordering': ['full_name', '-day_comes'],
                'unique_together': {('full_name', 'phone')},
            },
        ),
    ]
