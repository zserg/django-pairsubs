# Generated by Django 2.0.7 on 2018-07-05 17:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SubElement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num', models.IntegerField()),
                ('start', models.IntegerField()),
                ('end', models.IntegerField()),
                ('text', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='SubPair',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_start', models.IntegerField()),
                ('first_end', models.IntegerField()),
                ('second_start', models.IntegerField()),
                ('second_end', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Subs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movie_name', models.CharField(max_length=100)),
                ('sub_language_id', models.CharField(max_length=3)),
                ('sub_file_name', models.CharField(max_length=100)),
                ('id_movie_imdb', models.CharField(max_length=100)),
                ('id_sub_file', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='subpair',
            name='first_sub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='first_sub', to='pairsubs.Subs'),
        ),
        migrations.AddField(
            model_name='subpair',
            name='second_sub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='second_sub', to='pairsubs.Subs'),
        ),
        migrations.AddField(
            model_name='subelement',
            name='subtitles',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pairsubs.Subs'),
        ),
    ]