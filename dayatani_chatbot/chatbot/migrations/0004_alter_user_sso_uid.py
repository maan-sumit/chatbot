# Generated by Django 4.2.4 on 2023-08-08 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0003_user_is_active_user_is_staff_user_is_superuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='sso_uid',
            field=models.UUIDField(blank=True, null=True),
        ),
    ]