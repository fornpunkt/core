# Generated by Django 4.0 on 2022-01-07 00:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_alter_lamningtype_options_lamning_observation_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='lamning',
            name='title',
            field=models.TextField(default='glass', max_length=150),
            preserve_default=False,
        ),
    ]