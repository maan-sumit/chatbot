# Generated by Django 3.2 on 2023-09-14 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0008_auto_20230914_0830'),
    ]

    operations = [
        migrations.AlterField(
            model_name='files',
            name='url',
            field=models.URLField(max_length=400, null=True),
        ),
    ]