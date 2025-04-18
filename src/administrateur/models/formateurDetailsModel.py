from django.db import models
from django.core.exceptions import ValidationError
from .userModel import CustomUser
from .formationModel import Module

class Formateur_competence(models.Model):
    idformateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'type_utilisateur': 1, 'role_utilisateur':3})
    idmodule = models.ForeignKey(Module, on_delete=models.CASCADE)

    class Meta:
        db_table = "formateur_competence"

    def clean(self):
        if self.idformateur.role_utilisateur != 3:
            raise ValidationError("L'utilisateur sélectionné n'est pas un formateur")
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.idformateur.nom} - {self.idformateur.prenom} - {self.idmodule.module}"