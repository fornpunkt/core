# Generated by Django 4.0.4 on 2022-05-09 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_customtag_wikipedia'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lamning',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
    ]
