# Generated by Django 5.0.6 on 2024-07-09 10:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trade', '0006_alter_Recifitoken_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='Recifi',
            options={'ordering': ['-created_at']},
        ),
    ]