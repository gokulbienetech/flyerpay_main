# Generated by Django 5.0.6 on 2025-03-17 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0053_clients_zomato'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clients_zomato',
            name='client_name',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='clients_zomato',
            name='fp_zo_res_id',
            field=models.CharField(max_length=20),
        ),
    ]
