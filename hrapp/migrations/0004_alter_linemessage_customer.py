# Generated by Django 4.2.15 on 2024-08-23 09:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hrapp', '0003_rename_message_text_linemessage_messages_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linemessage',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_messages', to='hrapp.customer'),
        ),
    ]
