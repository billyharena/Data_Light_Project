from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.timezone import now

# Gestionnaire d'utilisateur personnalisé
class CustomUserManager(BaseUserManager):
    def create_user(self, email, nom, prenom, type_utilisateur, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        if type_utilisateur == 1:
            extra_fields.setdefault('is_staff', True) 
        user = self.model(email=email, nom=nom, prenom=prenom, type_utilisateur=type_utilisateur, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, prenom, password=None, **extra_fields):
        extra_fields.setdefault('role_utilisateur', 1)  # Superadmin
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email=email, nom=nom, prenom=prenom, type_utilisateur=1,password=password, **extra_fields)

# Utilisateur personnalisé
class CustomUser(AbstractBaseUser, PermissionsMixin):
    TYPE_UTILISATEUR_CHOICES = [
        (1, 'Admin'),
        (2, 'Client'),
    ]
    
    ROLE_UTILISATEUR_CHOICES = [
        (1, 'Superadmin'),
        (2, 'Admin'),
        (3, 'Formateur'),
        (4, 'Particulier'),
        (5, 'Entreprise'),
    ]

    # id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    type_utilisateur = models.IntegerField(choices=TYPE_UTILISATEUR_CHOICES)
    role_utilisateur = models.IntegerField(choices=ROLE_UTILISATEUR_CHOICES, null=True, blank=True)
    date_creation = models.DateTimeField(default=now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']

    class Meta:
        db_table = 'dl_user'

    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.email}"

"""
class LogtimeUtilisateur(models.Model):
    utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_debut = models.DateTimeField(default=now)
    date_fin = models.DateTimeField(null=True, blank=True)
    descriptions = models.TextField()

    class Meta:
        db_table = 'logtime_utilisateur'

    def __str__(self):
        return f"Logtime for {self.utilisateur.email} from {self.date_debut} to {self.date_fin}"
"""
# Détails pour les administrateurs
class DetailAdmin(models.Model):
    SEXE_CHOICES = [
        (1, 'Homme'),
        (2, 'Femme'),
    ]

    utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'type_utilisateur': 1})
    date_naissance = models.DateField()
    contact = models.CharField(max_length=50, blank=True, null=True)
    adresse = models.CharField(max_length=100)
    sexe = models.IntegerField(choices=SEXE_CHOICES)
    date_debut = models.DateTimeField(default=now)
    date_fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'detail_admin'

    def __str__(self):
        return f"Detail Admin for {self.utilisateur.email}"

# Détails pour les clients
class DetailClient(models.Model):
    SEXE_CHOICES = [
        (1, 'Homme'),
        (2, 'Femme'),
    ]

    TYPE_CLIENT_CHOICES = [
        (1, 'Particulier'),
        (2, 'Entreprise'),
    ]

    utilisateur = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'type_utilisateur': 2})
    date_naissance = models.DateField(blank=True, null=True)
    adresse = models.CharField(max_length=100, blank=True, null=True)
    contact = models.CharField(max_length=50, blank=True, null=True)
    cin = models.CharField(max_length=50, unique=True, blank=True, null=True)
    sexe = models.IntegerField(choices=SEXE_CHOICES)
    type_client = models.IntegerField(choices=TYPE_CLIENT_CHOICES)
    raison_social = models.CharField(max_length=100, blank=True, null=True)
    contact_entreprise = models.CharField(max_length=50, blank=True, null=True)
    date_creation_entreprise = models.DateField(blank=True, null=True)
    nif = models.CharField(max_length=50, unique=True, blank=True, null=True)
    stat = models.CharField(max_length=50, unique=True, blank=True, null=True)
    rcs = models.CharField(max_length=50, unique=True, blank=True, null=True)
    num_cnaps = models.CharField(max_length=100, unique=True, blank=True, null=True)
    effectif = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'detail_client'

    def __str__(self):
        return f"Detail Client pour {self.utilisateur.email}"