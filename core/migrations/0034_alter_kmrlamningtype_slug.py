# Generated by Django 4.1 on 2022-12-30 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_kmrlamningtype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kmrlamningtype',
            name='slug',
            field=models.SlugField(max_length=75),
        ),
    ]
