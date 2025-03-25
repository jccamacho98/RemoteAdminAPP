# Generated by Django 5.1.7 on 2025-03-25 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Info_PCs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=10, unique=True)),
                ('ip', models.CharField(blank=True, max_length=15, null=True)),
                ('mac_address', models.CharField(blank=True, max_length=17, null=True)),
                ('sistema_operativo', models.CharField(blank=True, max_length=50, null=True)),
                ('estado', models.CharField(choices=[('Online', 'Online'), ('Offline', 'Offline')], default='Offline', max_length=10)),
                ('domain_joined', models.BooleanField(default=False)),
                ('last_seen', models.DateTimeField(blank=True, null=True)),
                ('procesador', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'db_table': 'Info_PCs',
            },
        ),
    ]
