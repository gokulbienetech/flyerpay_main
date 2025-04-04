# Generated by Django 5.0.6 on 2025-03-27 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0071_rename_total_cpc_zomato_cpc_ads_cpc_value_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zomato_cpc_ads',
            name='cpc_value',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='zomato_cpc_ads',
            name='total_ads_inc_gst',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='zomato_cpc_ads',
            name='total_dining_ads',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
