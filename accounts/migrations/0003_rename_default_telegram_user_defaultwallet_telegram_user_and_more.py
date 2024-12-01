# Generated by Django 5.0.6 on 2024-05-29 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_userwallet_defaultwallet'),
    ]

    operations = [
        migrations.RenameField(
            model_name='defaultwallet',
            old_name='default_telegram_user',
            new_name='telegram_user',
        ),
        migrations.AlterField(
            model_name='userwallet',
            name='private_key',
            field=models.CharField(max_length=66),
        ),
    ]
