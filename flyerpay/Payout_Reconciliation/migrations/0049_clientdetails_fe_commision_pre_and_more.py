# Generated by Django 5.0.6 on 2025-03-17 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0048_sales_report_fp_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientdetails',
            name='fe_commision_pre',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='clientdetails',
            name='fp_res_id',
            field=models.CharField(default=1, max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='clientdetails',
            name='sw_commision_pre',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='clientdetails',
            name='zo_commision_pre',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
