from django.db import models
from .baseFacturation import DetailsBase, InscritBase, NonInscritBase
from administrateur.models.formationModel import Module
from ..userModel import CustomUser
from django.core.exceptions import ValidationError

# Table : FactureInscrit
class FactureInscrit(InscritBase):
    idclient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='FactureClient', limit_choices_to={'type_utilisateur': 2})
    reduction = models.FloatField(blank=True, null=True)
    paiement = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'facture_inscrit'
        verbose_name = 'Facture Inscrit'
        verbose_name_plural = 'Facture Inscripts'
        ordering = ['id' , 'date_creation']

    def __str__(self):
        return f"Facture client inscrit {self.id} - Client {self.idclient}"
    
    def clean(self):
        super().clean()
        if self.paiement and self.cout_total and self.paiement > self.cout_total:
            raise ValidationError({'paiement': "Le paiement ne peut pas être supérieur au coût total."})
    
# Table : FactureNonInscrit
class FactureNonInscrit(NonInscritBase):
    paiement = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'facture_non_inscrit'
        verbose_name = 'Facture Non Inscrit'
        verbose_name_plural = 'Facture Non Inscripts'
        ordering = ['id' , 'date_creation_pf']

    def clean(self):
        super().clean()
        if self.paiement and self.cout_total and self.paiement > self.cout_total:
            raise ValidationError({'paiement': "Le paiement ne peut pas être supérieur au coût total."})

# Table : FactureDetails
class FactureDetails(DetailsBase):
    idmodule = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='facture_modules')
    facture_inscrit = models.ForeignKey(FactureInscrit, on_delete=models.CASCADE, null=True, blank=True, related_name='details')
    facture_non_inscrit = models.ForeignKey(FactureNonInscrit, on_delete=models.CASCADE, null=True, blank=True, related_name='details')
    duree_seance = models.FloatField(blank=True, null=True)
    nbr_seance = models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = 'facture_detail'
        verbose_name = 'FactureDetail'
        verbose_name_plural = 'FactureDetails'

    def __str__(self):
        return f"Facture Details pour Module : {self.idmodule}"