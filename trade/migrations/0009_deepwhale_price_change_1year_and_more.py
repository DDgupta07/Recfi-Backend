# Generated by Django 5.0.6 on 2024-07-16 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade', '0008_rename_percentage_change_Recifi_pecentage_change_1year_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='Recifi',
            name='price_change_1year',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='Recifi',
            name='price_change_30days',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='Recifi',
            name='price_change_7days',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
