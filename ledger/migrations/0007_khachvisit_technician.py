# Generated by Django 5.0.1 on 2025-03-30 14:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0006_alter_supply_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='khachvisit',
            name='technician',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='donekhachvisits', to='ledger.technician'),
        ),
    ]
