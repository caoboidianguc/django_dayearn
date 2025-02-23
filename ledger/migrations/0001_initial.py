# Generated by Django 5.0.1 on 2025-02-23 08:54

import datetime
import django.core.validators
import django.db.models.deletion
import phonenumber_field.modelfields
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Khach',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=25)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('email', models.EmailField(blank=True, help_text='Enter your email for booking confirmations.', max_length=40, null=True)),
                ('points', models.PositiveIntegerField(default=0)),
                ('first_comes', models.DateTimeField(auto_now_add=True)),
                ('desc', models.TextField(blank=True, max_length=250, null=True)),
                ('status', models.CharField(choices=[('Confirmed', 'Online'), ('Anyone', 'Anyone'), ('Cancel', 'Cancel')], default='Confirmed', help_text='Choose anyone as an alternate!', max_length=20)),
                ('day_comes', models.DateField()),
                ('time_at', models.TimeField()),
                ('tag', models.CharField(blank=True, max_length=20, null=True)),
                ('birthday', models.DateField(blank=True, null=True)),
            ],
            options={
                'ordering': ['full_name', '-day_comes'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalTechnician',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('email', models.EmailField(blank=True, max_length=40, null=True)),
                ('start_work_at', models.TimeField()),
                ('end_work', models.TimeField()),
                ('isWork', models.BooleanField(default=False)),
                ('picture', models.TextField(max_length=100, null=True)),
                ('time_come_in', models.TimeField(null=True)),
                ('work_days', models.CharField(default='1111110', help_text='MTWTFSS: 1 for work, 0 for off', max_length=7)),
                ('vacation_start', models.DateField(blank=True, help_text='Start vacation', null=True)),
                ('vacation_end', models.DateField(blank=True, help_text='End vacation, back work!', null=True)),
                ('date_go_work', models.DateField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('owner', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical technician',
                'verbose_name_plural': 'historical technicians',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(validators=[django.core.validators.MinLengthValidator(1, "What's your message.")])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chats', to=settings.AUTH_USER_MODEL)),
                ('reply_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='ledger.chat')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='client_chats', to='ledger.khach')),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service', models.CharField(max_length=30)),
                ('price', models.FloatField()),
                ('time_perform', models.DurationField(default=datetime.timedelta(seconds=2700))),
                ('description', models.CharField(blank=True, max_length=800, null=True)),
                ('category', models.CharField(choices=[('Nail Enhancement', 'Nail'), ('Manicure', 'Mani'), ('Fix', 'Fix'), ('Wax', 'Wax'), ('Pedicure', 'Pedi')], default='Nail Enhancement', help_text='Choose one of the categories.', max_length=20)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['price'],
                'unique_together': {('service', 'price')},
            },
        ),
        migrations.AddField(
            model_name='khach',
            name='services',
            field=models.ManyToManyField(blank=True, related_name='khachs', to='ledger.service'),
        ),
        migrations.CreateModel(
            name='Technician',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('email', models.EmailField(blank=True, max_length=40, null=True)),
                ('start_work_at', models.TimeField()),
                ('end_work', models.TimeField()),
                ('isWork', models.BooleanField(default=False)),
                ('picture', models.ImageField(null=True, upload_to='tech_pictures/')),
                ('time_come_in', models.TimeField(null=True)),
                ('work_days', models.CharField(default='1111110', help_text='MTWTFSS: 1 for work, 0 for off', max_length=7)),
                ('vacation_start', models.DateField(blank=True, help_text='Start vacation', null=True)),
                ('vacation_end', models.DateField(blank=True, help_text='End vacation, back work!', null=True)),
                ('date_go_work', models.DateField(blank=True, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('services', models.ManyToManyField(blank=True, related_name='tech', to='ledger.service')),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'phone')},
            },
        ),
        migrations.AddField(
            model_name='khach',
            name='technician',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='khachs', to='ledger.technician'),
        ),
        migrations.CreateModel(
            name='HistoricalKhach',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('full_name', models.CharField(max_length=25)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('email', models.EmailField(blank=True, help_text='Enter your email for booking confirmations.', max_length=40, null=True)),
                ('points', models.PositiveIntegerField(default=0)),
                ('first_comes', models.DateTimeField(blank=True, editable=False)),
                ('desc', models.TextField(blank=True, max_length=250, null=True)),
                ('status', models.CharField(choices=[('Confirmed', 'Online'), ('Anyone', 'Anyone'), ('Cancel', 'Cancel')], default='Confirmed', help_text='Choose anyone as an alternate!', max_length=20)),
                ('day_comes', models.DateField()),
                ('time_at', models.TimeField()),
                ('tag', models.CharField(blank=True, max_length=20, null=True)),
                ('birthday', models.DateField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('technician', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ledger.technician')),
            ],
            options={
                'verbose_name': 'historical khach',
                'verbose_name_plural': 'historical khachs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='ledger.chat')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='liked_chats', to='ledger.khach')),
            ],
            options={
                'unique_together': {('chat', 'client')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='khach',
            unique_together={('full_name', 'phone')},
        ),
    ]
