# Generated by Django 5.0.6 on 2025-03-12 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0029_rename_total_zomato_orders_reconciliationsummary_total_orders'),
    ]

    operations = [
        migrations.AddField(
            model_name='reconciliationsummary',
            name='from_date',
            field=models.DateField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reconciliationsummary',
            name='to_date',
            field=models.DateField(default=1),
            preserve_default=False,
        ),
    ]
