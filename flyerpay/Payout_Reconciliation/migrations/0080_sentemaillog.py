# Generated by Django 5.0.6 on 2025-04-07 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Payout_Reconciliation', '0079_rename_sales_report_zomato_sales_report'),
    ]

    operations = [
        migrations.CreateModel(
            name='SentEmailLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('sender', models.EmailField(max_length=254)),
                ('recipients', models.TextField()),
                ('cc', models.TextField(blank=True, null=True)),
                ('bcc', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
