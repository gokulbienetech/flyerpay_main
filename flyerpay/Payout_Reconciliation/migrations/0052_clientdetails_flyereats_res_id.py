# Generated by Django 5.0.6 on 2025-03-17 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0051_rename_fp_res_id_clientdetails_swiggy_res_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientdetails',
            name='flyereats_res_id',
            field=models.CharField(default=1, max_length=20),
            preserve_default=False,
        ),
    ]
