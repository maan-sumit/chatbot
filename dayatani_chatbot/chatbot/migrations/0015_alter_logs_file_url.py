# Generated by Django 3.2 on 2023-09-25 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0014_logs_file_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logs',
            name='file_url',
            field=models.URLField(max_length=400, null=True),
        ),
    ]
