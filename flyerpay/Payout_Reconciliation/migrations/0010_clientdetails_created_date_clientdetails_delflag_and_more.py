# Generated by Django 5.0.6 on 2025-03-08 06:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0009_aggregator'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientdetails',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='clientdetails',
            name='delflag',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='clientdetails',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
