# Generated by Django 5.0.6 on 2025-03-29 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0074_rename_aggregator_payment_mechanism_fee_aggregator_payment_mechanism_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='aggregator',
            name='payment_mechanism_fee_online',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
