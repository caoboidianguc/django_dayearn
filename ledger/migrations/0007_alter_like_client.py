# Generated by Django 5.0.1 on 2025-03-14 19:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0006_alter_like_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='liked_chats', to='ledger.khach'),
        ),
    ]
