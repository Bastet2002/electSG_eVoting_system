# Generated by Django 4.2.13 on 2024-07-19 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_webauthnregistration_webauthncredentials'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='first_login',
            field=models.BooleanField(default=True),
        ),
    ]
