from rest_framework import serializers
from administrateur.models import CustomUser, DetailClient
from django.contrib.auth.password_validation import validate_password

class ClientRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    type_client = serializers.IntegerField(required=True)
    sexe = serializers.IntegerField(required=False, allow_null=True)  # Facultatif pour une entreprise
    raison_social = serializers.CharField(required=False, allow_blank=True)  # Nom entreprise
    contact_entreprise = serializers.CharField(required=False, allow_blank=True)
    date_creation_entreprise = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = ('nom', 'prenom', 'email', 'password', 'type_client', 'sexe', 
                  'raison_social', 'contact_entreprise', 'date_creation_entreprise')

    def validate(self, data):
        if data['type_client'] == 1:  # Particulier
            if not data.get('nom') or not data.get('prenom'):
                raise serializers.ValidationError("Le nom et le prénom sont obligatoires pour un particulier.")
            if 'sexe' not in data:
                raise serializers.ValidationError("Le sexe est obligatoire pour un particulier.")
        else:  # Entreprise
            if not data.get('raison_social'):
                raise serializers.ValidationError("La raison sociale est obligatoire pour une entreprise.")
        
        return data

    def create(self, validated_data):
        type_client = validated_data['type_client']

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            nom=validated_data['nom'] if type_client == 1 else validated_data['raison_social'],
            prenom=validated_data['prenom'] if type_client == 1 else '',
            type_utilisateur=2,
            password=validated_data['password'],
            role_utilisateur=4 if type_client == 1 else 5
        )

        DetailClient.objects.create(
            utilisateur=user,
            sexe=validated_data.get('sexe') if type_client == 1 else None,
            type_client=type_client,
            raison_social=validated_data.get('raison_social', None),
            contact_entreprise=validated_data.get('contact_entreprise', None),
            date_creation_entreprise=validated_data.get('date_creation_entreprise', None),
        )

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

# class ClientUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DetailClient
#         fields = ['date_naissance', 'adresse', 'contact', 'cin', 'sexe', 'type_client', 'raison_social', 'contact_entreprise', 'date_creation_entreprise', 'nif', 'stat', 'rcs', 'num_cnaps', 'effectif']


class ClientProfileSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(source='utilisateur.nom', read_only=True)
    prenom = serializers.CharField(source='utilisateur.prenom', read_only=True)
    email = serializers.EmailField(source='utilisateur.email', read_only=True)

    class Meta:
        model = DetailClient
        fields = '__all__'
        read_only_fields = ['utilisateur']
    
    def validate(self, data):
        user = self.instance.utilisateur
        if user.type_utilisateur == 2:  # Client
            if user.role_utilisateur == 4:  # Particulier
                allowed_fields = {'contact', 'adresse', 'cin', 'utilisateur'}
            else:  # Entreprise
                allowed_fields = {'raison_social', 'contact_entreprise', 'date_creation_entreprise',
                                  'nif', 'stat', 'rcs', 'num_cnaps', 'effectif', 'utilisateur', 'adresse'}
            
            for field in data.keys():
                if field not in allowed_fields:
                    raise serializers.ValidationError({field: "Modification non autorisée pour ce champ."})
        return data
    
class ClientProfileUpdateSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(source='utilisateur.nom', required=False)
    prenom = serializers.CharField(source='utilisateur.prenom', required=False)
    email = serializers.EmailField(source='utilisateur.email', required=False)

    class Meta:
        model = DetailClient
        fields = '__all__'
        read_only_fields = ['utilisateur']  # Empêcher la modification de l'utilisateur lié

    def update(self, instance, validated_data):
        user_data = validated_data.pop('utilisateur', {})

        # Mise à jour des champs du modèle CustomUser
        user = instance.utilisateur
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Mise à jour des champs du modèle DetailClient
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
