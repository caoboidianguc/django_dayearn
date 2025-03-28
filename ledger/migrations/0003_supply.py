# Generated by Django 5.0.1 on 2025-03-27 22:06

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0002_alter_like_unique_together_chat_isnew_like_owner_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Supply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=42, validators=[django.core.validators.MinLengthValidator(2)])),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('info', models.CharField(max_length=250, null=True)),
                ('price', models.FloatField(max_length=10, null=True)),
                ('is_wanted', models.BooleanField(default=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplies', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
