# Generated by Django 5.0.6 on 2025-03-08 07:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0016_alter_clientdetails_create_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clientdetails',
            name='create_date',
        ),
        migrations.RemoveField(
            model_name='clientdetails',
            name='updated_date',
        ),
    ]
