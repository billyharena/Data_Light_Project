# Generated by Django 5.1.4 on 2025-01-23 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrateur', '0012_facturedetails_duree_seance_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='proformanoninscrit',
            name='etat',
            field=models.IntegerField(choices=[(0, 'Non facturé'), (1, 'Facturé')], default=0),
        ),
    ]
