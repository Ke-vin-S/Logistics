# Generated by Django 5.2 on 2025-05-09 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmentitem',
            name='role',
            field=models.CharField(choices=[('pickup', 'Pickup'), ('delivery', 'Delivery')], default='delivery', max_length=10),
        ),
    ]
