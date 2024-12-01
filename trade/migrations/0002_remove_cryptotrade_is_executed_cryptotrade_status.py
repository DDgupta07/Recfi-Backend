# Generated by Django 5.0.6 on 2024-06-17 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cryptotrade',
            name='is_executed',
        ),
        migrations.AddField(
            model_name='cryptotrade',
            name='status',
            field=models.CharField(choices=[('open', 'Open'), ('closed', 'Closed'), ('failed', 'Failed')], default='open', max_length=50),
        ),
    ]