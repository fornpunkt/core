# Generated by Django 4.0 on 2022-01-01 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_lamningtype_description_lamningtype_wikipedia'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lamningtype',
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='lamning',
            name='observation_type',
            field=models.CharField(blank=True, choices=[('FO', 'Fältobservation'), ('RO', 'Fjärrobservation')], max_length=2),
        ),
    ]
