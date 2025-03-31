# Generated by Django 5.0.6 on 2025-03-10 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0023_remove_clientdetails_partnership_vendor_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientdetails',
            name='fe_escalation_manager',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='clientdetails',
            name='fe_finance_poc',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='clientdetails',
            name='swiggy_escalation_manager',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='clientdetails',
            name='swiggy_finance_poc',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='clientdetails',
            name='zomato_escalation_manager',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='clientdetails',
            name='zomato_finance_poc',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
