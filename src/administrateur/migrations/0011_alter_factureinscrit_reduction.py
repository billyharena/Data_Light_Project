# Generated by Django 5.1.4 on 2025-01-23 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrateur', '0010_facturenoninscrit_frais_transport_proformanoninscrit_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factureinscrit',
            name='reduction',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
