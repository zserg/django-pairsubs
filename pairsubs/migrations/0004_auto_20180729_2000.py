# Generated by Django 2.0.7 on 2018-07-29 20:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pairsubs', '0003_auto_20180707_0858'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SubPair',
            new_name='PairOfSubs',
        ),
    ]
