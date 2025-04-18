import os
from django.db import models
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField
from django.utils import timezone
# from userModel import CustomUser

class Formation(models.Model):
    formation = models.CharField(max_length=50)
    descriptions = RichTextField()
    img = models.ImageField(upload_to='formations/')
    disponibilite = models.BooleanField(default=True)

    class Meta:
        db_table = 'formation'
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'
        ordering = ['id', 'disponibilite']

    def save(self, *args, **kwargs):
        # Si une nouvelle image est définie, on supprime l'ancienne image
        if self.pk:
            old_formation = Formation.objects.get(pk=self.pk)
            old_image = old_formation.img
            new_image = self.img

            if old_image != new_image and old_image and os.path.isfile(old_image.path):
                os.remove(old_image.path)

        # Sauvegarder l'instance avec la nouvelle image
        super(Formation, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.formation}"
    
class Module(models.Model):
    idformation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='modules')
    module = models.CharField(max_length=50)
    img = models.ImageField(upload_to='modules/')  # Stockage d'images
    descriptions = RichTextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)  # Utilisation de DecimalField pour plus de précision
    duree = models.DecimalField(max_digits=5, decimal_places=2)  # Durée en heures ou jours
    disponibilite = models.BooleanField(default=True)

    class Meta:
        db_table = "module"
        verbose_name = "Module de formation"
        verbose_name_plural = "Modules de formation"
        ordering = ['id', 'idformation']

    def __str__(self):
        return f"{self.module} (Formation : {self.idformation.formation})"

    def clean(self):
        # Vérifiez que le prix n'est pas négatif
        if self.prix < 0:
            raise ValidationError({'prix': "Le prix ne peut pas être négatif."})

        # Vérifiez que la durée n'est pas négative
        if self.duree < 0:
            raise ValidationError({'duree': "La durée ne peut pas être négative."})
        
    def has_active_promotions(self):
        return self.promotions.filter(dateDebut__lte=timezone.now(), dateFin__gte=timezone.now()).exists()

    has_active_promotions.boolean = True  # Affiche une icône "Oui" ou "Non" dans l'admin
    has_active_promotions.short_description = 'En promotion'

# class Avis(models.Model):
#     note = models.IntegerField(null=False, default=0)
#     avis = RichTextField()
#     client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'type_utilisateur': 2})

#     class Meta:
#         db_table = 'avis'
#         verbose_name = 'Avis'
#         verbose_name_plural = 'Avis'
#         ordering = ['id', 'note']