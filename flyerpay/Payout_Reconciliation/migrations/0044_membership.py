# Generated by Django 5.0.6 on 2025-03-13 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0043_remove_sales_report_swiggy_created_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('membership_type', models.CharField(choices=[('Monthly', 'Monthly'), ('Yearly', 'Yearly'), ('One Time', 'One Time')], max_length=20)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('delflag', models.IntegerField(default=1)),
            ],
        ),
    ]
