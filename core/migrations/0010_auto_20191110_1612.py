# Generated by Django 2.2.5 on 2019-11-10 16:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20191110_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='lamning',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Lamning'),
        ),
    ]
