# Generated by Django 5.0.1 on 2025-03-05 22:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='client_chats', to='ledger.khach'),
        ),
    ]
