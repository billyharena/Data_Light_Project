from django.db import models
from administrateur.models.formationModel import Module
from django.core.exceptions import ValidationError
from datetime import date
from django.utils.timezone import now

class Extra(models.Model):
    MOTIF_CHOICES = [
        (1, "Transport"),
        (2, "PC"),
        (3, "restauration")
    ]
    DETAIL_CHOICES = [
        (1, "Antananarivo-Local Data Light"),
        (2, "Antananarivo-Périphérie"),
        (3, "Antananarivo-Centre ville"),
        (4, "Région")
    ]
    motif = models.IntegerField(choices=MOTIF_CHOICES)
    details = models.IntegerField(choices=DETAIL_CHOICES, blank=True, null=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "extra"
        ordering = ['motif']

    def clean(self):
        if self.prix < 0 :
            raise ValidationError({'message': "Prix négatif!"})
        
class StockPC(models.Model):
    stock = models.IntegerField(blank=True, null=True)
    class Meta:
        db_table = "stock_pc"

# Classe abstraite pour les tables Inscrit (ProformaInscrit et FactureInscrit)
class InscritBase(models.Model):
    id_createur = models.IntegerField(blank=True, null=True)
    lieu_formation = models.CharField(max_length=150)
    nbr_location_pc = models.IntegerField(default=0, blank=True, null=True)
    pu_pc = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    nbr_frais_transport = models.FloatField(blank=True, null=True)
    pu_transport = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    nbr_frais_restauration = models.FloatField(blank=True, null=True)
    pu_restauration =models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hebergement = models.FloatField(blank=True, null=True)
    pu_hebergement = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date_creation = models.DateField(default=now)
    cout_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    class Meta:
        abstract = True

    def clean(self):
        # Vérifiez que le prix n'est pas négatif
        if self.nbr_location_pc < 0 or self.pu_pc < 0 or self.nbr_frais_transport < 0 or self.pu_transport < 0 or self.nbr_frais_restauration < 0 or self.pu_restauration < 0 or self.hebergement < 0 or self.pu_hebergement < 0:
            raise ValidationError({'message': "Vérifier la cohérence de vos données !"})
        
    def get_extra_from_location(self):
        for choice in Extra.DETAIL_CHOICES:
            if choice[1] == self.lieu_formation:
                return choice[0]
        return 1  # Valeur par défaut

# Classe abstraite pour les tables NonInscrit (ProformaNonInscrit et FactureNonInscrit)
class NonInscritBase(models.Model):
    id_createur = models.IntegerField(blank=True, null=True)
    nom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)
    nom_entreprise = models.CharField(max_length=100, blank=True, null=True)
    adresse_entreprise = models.CharField(max_length=100, blank=True, null=True)
    date_creation = models.DateField(null=True, blank=True)
    contact = models.CharField(max_length=50, blank=True)
    nif = models.CharField(max_length=50, blank=True, null=True)
    stat = models.CharField(max_length=50, blank=True, null=True)
    rcs = models.CharField(max_length=50, blank=True, null=True)
    cnaps = models.CharField(max_length=150, blank=True, null=True)
    lieu_formation = models.CharField(max_length=150)
    nbr_location_pc = models.IntegerField(default=0, blank=True, null=True)
    pu_pc = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    nbr_frais_transport = models.FloatField(blank=True, null=True)
    pu_transport = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    nbr_frais_restauration = models.FloatField(blank=True, null=True)
    pu_restauration = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    hebergement = models.FloatField(blank=True, null=True)
    pu_hebergement = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date_creation_pf = models.DateField(auto_now_add=True)
    cout_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    class Meta:
        abstract = True

    def get_extra_from_location(self):
        for choice in Extra.DETAIL_CHOICES:
            if choice[1] == self.lieu_formation:
                return choice[0]
        return 1  # Valeur par défaut

    def clean(self):
        # Vérifiez que le prix n'est pas négatif
        if self.nbr_location_pc < 0 or self.pu_pc < 0 or self.nbr_frais_transport < 0 or self.pu_transport < 0 or self.nbr_frais_restauration < 0 or self.pu_restauration < 0 or self.hebergement < 0 or self.pu_hebergement < 0:
            raise ValidationError({'message': "Vérifier la cohérence de vos données !"})
        
    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.nom_entreprise}"
    
# Classe abstraite pour les tables Details (ProformaDetails et FactureDetails)
class DetailsBase(models.Model):
    idmodule = models.ForeignKey(Module, on_delete=models.CASCADE)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantite = models.IntegerField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.prix_unitaire is None and self.idmodule:
            self.prix_unitaire = self.idmodule.prix
        super().save(*args, **kwargs)

    # def clean(self):
    #     if self.date_deb <= date.today():
    #         raise ValidationError({'date_deb': "La date de début ne peut pas être inférieur à celle d'aujourdhui."})
    #     if self.date_fin <= self.date_deb:
    #         raise ValidationError({'date_fin' : "La date fin ne peut être inférieur à la date de début !"})