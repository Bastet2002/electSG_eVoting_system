# Generated by Django 4.2.13 on 2024-05-27 03:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_alter_useraccount_username'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useraccount',
            name='user_id',
        ),
    ]