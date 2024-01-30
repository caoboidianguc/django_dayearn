# Generated by Django 5.0.1 on 2024-01-27 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0003_alter_khach_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='khach',
            name='status',
            field=models.CharField(choices=[('WebSite', 'Online'), ('Anyone', 'Anyone'), ('Cancel', 'Cancel')], default='WebSite', max_length=20),
        ),
    ]
