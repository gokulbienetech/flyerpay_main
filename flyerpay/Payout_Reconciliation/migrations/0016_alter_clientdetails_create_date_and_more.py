# Generated by Django 5.0.6 on 2025-03-08 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0015_clientdetails_create_date_clientdetails_updated_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientdetails',
            name='create_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='clientdetails',
            name='updated_date',
            field=models.DateTimeField(null=True),
        ),
    ]
