# Generated by Django 3.2.9 on 2021-11-23 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20191110_1612'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created_time']},
        ),
        migrations.AddField(
            model_name='lamningtype',
            name='raa_id',
            field=models.IntegerField(default=123),
            preserve_default=False,
        ),
    ]