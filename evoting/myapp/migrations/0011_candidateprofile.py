# Generated by Django 4.2.13 on 2024-06-03 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_alter_useraccount_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('election_poster', models.ImageField(blank=True, null=True, upload_to='election_posters/')),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('candidate_statement', models.TextField(blank=True)),
                ('user_account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='myapp.useraccount')),
            ],
        ),
    ]