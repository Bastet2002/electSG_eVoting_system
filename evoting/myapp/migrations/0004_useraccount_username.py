# Generated by Django 4.2.13 on 2024-05-27 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_electionphase'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='username',
            field=models.CharField(default='default_UN', max_length=200, unique=True),
        ),
    ]
