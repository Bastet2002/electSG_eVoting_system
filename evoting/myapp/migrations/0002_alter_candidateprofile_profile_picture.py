# Generated by Django 4.2.13 on 2024-07-16 03:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidateprofile',
            name='profile_picture',
            field=models.ImageField(upload_to='profile_pictures/'),
        ),
    ]
