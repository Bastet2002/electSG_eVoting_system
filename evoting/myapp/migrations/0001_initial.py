# Generated by Django 4.2.13 on 2024-07-20 19:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserAccount',
            fields=[
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('user_id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=200, unique=True)),
                ('password', models.CharField(max_length=200)),
                ('full_name', models.CharField(max_length=200)),
                ('date_of_birth', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('announcement_id', models.AutoField(primary_key=True, serialize=False)),
                ('header', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('district_id', models.AutoField(primary_key=True, serialize=False)),
                ('district_name', models.CharField(max_length=255)),
                ('num_of_people', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ElectionPhase',
            fields=[
                ('phase_id', models.AutoField(primary_key=True, serialize=False)),
                ('phase_name', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('party_id', models.AutoField(primary_key=True, serialize=False)),
                ('party_name', models.CharField(max_length=255)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('profile_id', models.AutoField(primary_key=True, serialize=False)),
                ('profile_name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SingpassUser',
            fields=[
                ('singpass_id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=255)),
                ('full_name', models.CharField(max_length=255)),
                ('date_of_birth', models.DateField()),
                ('phone_num', models.CharField(max_length=20)),
                ('district', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='CandidateProfile',
            fields=[
                ('candidate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('election_poster', models.ImageField(blank=True, null=True, upload_to='election_posters/')),
                ('candidate_statement', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CandidatePublicKey',
            fields=[
                ('candidate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('pkv', models.CharField(max_length=64)),
                ('pks', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='VoteResults',
            fields=[
                ('candidate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('total_vote', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='WebauthnRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('challenge', models.CharField(blank=True, max_length=9000, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WebauthnCredentials',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credential_id', models.CharField(blank=True, max_length=9000, null=True)),
                ('credential_public_key', models.CharField(blank=True, max_length=9000, null=True)),
                ('current_sign_count', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webauthn_credentials', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='VotingCurrency',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('stealth_address', models.CharField(max_length=64, unique=True)),
                ('commitment_record', models.JSONField()),
                ('district', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.district')),
            ],
        ),
        migrations.CreateModel(
            name='VoteRecords',
            fields=[
                ('key_image', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('transaction_record', models.JSONField()),
                ('district', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.district')),
            ],
        ),
        migrations.CreateModel(
            name='Voter',
            fields=[
                ('voter_id', models.AutoField(primary_key=True, serialize=False)),
                ('hash_from_info', models.CharField(max_length=128, null=True, unique=True)),
                ('pkv', models.CharField(max_length=64)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('district', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.district')),
            ],
        ),
        migrations.AddField(
            model_name='useraccount',
            name='district',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.district'),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='party',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.party'),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.profile'),
        ),
    ]
