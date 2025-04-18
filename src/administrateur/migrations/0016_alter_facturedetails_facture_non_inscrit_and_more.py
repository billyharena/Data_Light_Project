# Generated by Django 5.1.4 on 2025-01-24 05:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrateur', '0015_alter_factureinscrit_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facturedetails',
            name='facture_non_inscrit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='details', to='administrateur.facturenoninscrit'),
        ),
        migrations.CreateModel(
            name='PlanningFormation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dateFormation', models.DateField()),
                ('heureDebFormation', models.TimeField()),
                ('heureFinFormation', models.TimeField()),
                ('etat', models.IntegerField(choices=[(0, 'À venir'), (1, 'Terminée'), (2, 'Reportée'), (-1, 'Annulée')], default=0)),
                ('commentaire', models.TextField(blank=True, null=True)),
                ('idfacturedetail', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planning_details', to='administrateur.facturedetails')),
                ('idformateur', models.ForeignKey(limit_choices_to={'role_utilisateur': 3}, on_delete=django.db.models.deletion.CASCADE, related_name='planning_formateur', to=settings.AUTH_USER_MODEL)),
                ('idmodule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planning_modules', to='administrateur.module')),
            ],
            options={
                'verbose_name': 'Planning de Formation',
                'verbose_name_plural': 'Plannings de Formation',
                'db_table': 'planning_formation',
                'ordering': ['dateFormation', 'heureDebFormation', 'idformateur'],
            },
        ),
    ]
