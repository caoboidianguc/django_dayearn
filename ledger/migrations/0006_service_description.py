# Generated by Django 5.0.1 on 2024-02-02 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0005_alter_chat_client_alter_chat_tech_alter_chat_text_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='description',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
