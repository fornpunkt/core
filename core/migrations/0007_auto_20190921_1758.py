# Generated by Django 2.2.5 on 2019-09-21 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='lamning',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='core.Lamning'),
        ),
    ]
