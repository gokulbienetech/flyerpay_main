# Generated by Django 5.0.6 on 2025-04-05 12:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0078_rename_fp_client_name_sales_report_zomato_client_name_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='sales_report_zomato',
            new_name='sales_report',
        ),
    ]
