from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from .formationModel import Module
from .facturation.facture import FactureDetails
from .formateurDetailsModel import Formateur_competence
from .userModel import CustomUser
from datetime import datetime, timedelta, time, date

class PlanningFormation(models.Model):
    ETAT_CHOICES = [
        (0, 'À venir'),
        (1, 'Terminée'),
        (2, 'Reportée'),
        (-1, 'Annulée'),
    ]

    idformateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role_utilisateur': 3}, related_name='planning_formateur')
    idmodule = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='planning_modules')
    idfacturedetail = models.ForeignKey(FactureDetails, on_delete=models.CASCADE, related_name='planning_details')
    dateFormation = models.DateField()
    heureDebFormation = models.TimeField()
    heureFinFormation = models.TimeField()
    etat = models.IntegerField(choices=ETAT_CHOICES, default=0)
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'planning_formation'
        verbose_name = 'Planning de Formation'
        verbose_name_plural = 'Plannings de Formation'
        ordering = ['dateFormation', 'heureDebFormation', 'idformateur']

    def __str__(self):
        return f"Planning - Formateur: {self.idformateur.nom} {self.idformateur.prenom}, Module: {self.idmodule.module} ({self.dateFormation} {self.heureDebFormation} - {self.heureFinFormation})"

    def clean(self):
        # Conversion de dateFormation en objet date si nécessaire
        if isinstance(self.dateFormation, str):
            try:
                self.dateFormation = datetime.strptime(self.dateFormation, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError({'dateFormation': "Format de date invalide. Utilisez le format YYYY-MM-DD."})

        # Vérifier si la date est un jour ouvrable ou un samedi
        if self.dateFormation.weekday() not in range(0, 6):  # 0-4 pour lundi-vendredi, 5 pour samedi
            raise ValidationError({
                'dateFormation': "La date de formation doit être un jour ouvrable (lundi à vendredi) ou un samedi."
            })

        # Vérifier si les horaires sont valides
        if self.heureDebFormation >= self.heureFinFormation:
            raise ValidationError({'heureDebFormation': "L'heure de début doit être antérieure à l'heure de fin."})

    def save(self, *args, **kwargs):
        self.clean()  # Appeler explicitement clean avant la sauvegarde
        super().save(*args, **kwargs)



# def get_workdays_of_month(year, month):
#     first_day = datetime(year, month, 1)
#     last_day = (first_day + timedelta(days=31)).replace(day=1) - timedelta(days=1)
#     workdays = []
#     for n in range((last_day - first_day).days + 1):
#         day = first_day + timedelta(n)
#         if day.weekday() < 5:  # Lundi (0) à Vendredi (4)
#             workdays.append(day)
#     return workdays

# def get_formateurs_competents(module_id):
#     """Retourne les formateurs ayant les compétences pour un module donné."""
#     return CustomUser.objects.filter(
#         id__in=Formateur_competence.objects.filter(idmodule=module_id).values_list('idformateur', flat=True),
#         is_active=True
#     )

# def get_formateur_disponibilite(formateur, date):
#     """Retourne les créneaux horaires occupés d’un formateur pour une date donnée."""
#     plannings = PlanningFormation.objects.filter(
#         idformateur=formateur,
#         dateFormation=date
#     ).order_by('heureDebFormation')

#     occupied_slots = [(p.heureDebFormation, p.heureFinFormation) for p in plannings]
#     return occupied_slots

# def calculate_free_slots(occupied_slots):
#     """Calcule les créneaux libres en excluant les créneaux occupés."""
#     start_time = time(8, 0)  # Début de la journée (8:00)
#     end_time = time(18, 0)  # Fin de la journée (18:00)
#     free_slots = []

#     current_time = start_time
#     for start, end in occupied_slots:
#         if current_time < start:
#             free_slots.append((current_time, start))
#         current_time = max(current_time, end)

#     if current_time < end_time:
#         free_slots.append((current_time, end_time))

#     return free_slots

# def find_free_slots_for_module(year, month, module_id):
#     """Retourne les créneaux libres par jour pour tous les formateurs compétents."""
#     workdays = get_workdays_of_month(year, month)
#     formateurs = get_formateurs_competents(module_id)
#     free_slots_by_day = {}

#     for day in workdays:
#         free_slots_by_day[day] = []
#         for formateur in formateurs:
#             occupied_slots = get_formateur_disponibilite(formateur, day)
#             free_slots = calculate_free_slots(occupied_slots)
#             if free_slots:
#                 free_slots_by_day[day].append({
#                     "formateur": f"{formateur.nom} {formateur.prenom}",
#                     "slots": free_slots
#                 })

#     return free_slots_by_day