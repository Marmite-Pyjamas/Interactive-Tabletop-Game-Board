# Generated by Django 4.0.3 on 2022-05-02 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('playerId', models.CharField(max_length=1000)),
                ('pieceId', models.CharField(max_length=1000)),
                ('pieceName', models.CharField(max_length=1000)),
                ('xyCords', models.CharField(max_length=1000)),
            ],
        ),
    ]
