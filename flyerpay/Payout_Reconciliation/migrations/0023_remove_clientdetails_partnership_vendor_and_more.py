# Generated by Django 5.0.6 on 2025-03-10 05:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0022_alter_clientdetails_business_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clientdetails',
            name='partnership_vendor',
        ),
        migrations.AddField(
            model_name='clientdetails',
            name='partnership_vendor',
            field=models.ManyToManyField(related_name='clients', to='Payout_Reconciliation.aggregator'),
        ),
    ]
