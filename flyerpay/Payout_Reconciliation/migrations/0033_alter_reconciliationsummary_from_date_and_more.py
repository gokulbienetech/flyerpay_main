# Generated by Django 5.0.6 on 2025-03-12 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0032_reconciliationsummary_from_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reconciliationsummary',
            name='from_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='reconciliationsummary',
            name='to_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
