# Generated by Django 4.0.6 on 2022-07-07 09:50

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("Happyface4", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="WarningLevels",
            new_name="InstanceStatus",
        ),
    ]
