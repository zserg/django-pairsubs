# Generated by Django 2.0.7 on 2018-07-05 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pairsubs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subelement',
            name='text',
            field=models.CharField(max_length=220),
        ),
    ]