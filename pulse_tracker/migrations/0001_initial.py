# Generated by Django 5.0.6 on 2024-06-14 13:05

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0006_userwallet_is_verified'),
    ]

    operations = [
        migrations.CreateModel(
            name='WatchList',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, editable=False, null=True)),
                ('contract_address', models.CharField(max_length=75)),
                ('symbol', models.CharField(max_length=20)),
                ('telegram_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='watchlist', to='accounts.telegramuser')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
