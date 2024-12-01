# Generated by Django 5.0.6 on 2024-05-27 10:24

import django.contrib.postgres.fields
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserWallet',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('wallet_name', models.CharField(max_length=255)),
                ('wallet_phrase_key', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), blank=True, null=True, size=None)),
                ('wallet_address', models.CharField(max_length=50)),
                ('private_key', models.CharField(max_length=64)),
                ('telegram_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_wallet', to='accounts.telegramuser')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DefaultWallet',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('default_telegram_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='default_wallet', to='accounts.telegramuser')),
                ('user_wallet', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='accounts.userwallet')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
