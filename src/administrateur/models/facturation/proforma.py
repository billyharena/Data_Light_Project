from django.db import models
from .baseFacturation import DetailsBase, InscritBase, NonInscritBase
from administrateur.models.formationModel import Module
from ..userModel import CustomUser

# Table : ProformaInscrit
class ProformaInscrit(InscritBase):
    ETAT_CHOICE = [
        (0, "Non facturé"),
        (1, "Facturé")
    ]

    idclient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ProformaClient', limit_choices_to={'type_utilisateur': 2})
    facture = models.IntegerField(blank=True, null=True)
    etat = models.IntegerField(choices=ETAT_CHOICE, default=0)
    reduction = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'proforma_inscrit'
        verbose_name = 'Proforma des inscrits'
        verbose_name_plural = 'Proformas des inscripts'
        ordering = ['id' , 'date_creation']

    def __str__(self):
        return f"ProformaInscrit {self.id} - Client {self.idclient}"

# Table : ProformaNonInscrit
class ProformaNonInscrit(NonInscritBase):
    ETAT_CHOICE = [
        (0, "Non facturé"),
        (1, "Facturé")
    ]
    facture_non_inscrit = models.IntegerField(blank=True, null=True)
    etat = models.IntegerField(choices=ETAT_CHOICE, default=0)
    class Meta:
        db_table = 'proforma_non_inscrit'
        verbose_name = 'Proforma pour les non-inscrit'
        verbose_name_plural = 'Proformas des non-inscripts'
        ordering = ['id' , 'date_creation_pf']

# Table : ProformaDetails
class ProformaDetails(DetailsBase):
    idmodule = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='proforma_modules')
    proforma_inscrit = models.ForeignKey(
        ProformaInscrit, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='details'  # Permet d'accéder aux détails via proforma_inscrit.details
    )

    proforma_non_inscrit = models.ForeignKey(
        ProformaNonInscrit, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='details'  # Permet d'accéder aux détails via proforma_non_inscrit.details
    )
    duree_seance = models.FloatField(blank=True, null=True)
    nbr_seance = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'proforma_detail'
        verbose_name = 'Proforma Detail'
        verbose_name_plural = 'Proforma Details'

    def __str__(self):
        return f"ProformaDetails for Module {self.idmodule}"