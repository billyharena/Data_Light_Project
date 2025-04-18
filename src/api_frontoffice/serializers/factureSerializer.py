from rest_framework import serializers
from administrateur.models.facturation import FactureNonInscrit, FactureDetails, FactureInscrit
from administrateur.models.formationModel import Module

class FactureDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactureDetails
        fields = ['idmodule', 'prix_unitaire', 'quantite', 'duree_seance', 'nbr_seance']

class FactureNonInscritSerializer(serializers.ModelSerializer):
    details = FactureDetailsSerializer(many=True)
    cout_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = FactureNonInscrit
        fields = [
            'nom', 'prenom', 'email', 'lieu_formation', 'pu_pc', 'paiement', 'details', 'cout_total'
        ]

    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        facture = FactureNonInscrit.objects.create(**validated_data)

        cout_total = 0

        for detail in details_data:
            prix_unitaire = detail.get('prix_unitaire', 0)
            quantite = detail.get('quantite', 1)
            montant_detail = prix_unitaire * quantite

            FactureDetails.objects.create(facture_non_inscrit=facture, **detail)

            cout_total += montant_detail

        # Mise à jour du coût total
        facture.cout_total = cout_total

        # Vérifier que le paiement ne dépasse pas le coût total
        paiement = validated_data.get('paiement', 0) or 0
        if paiement > cout_total:
            raise serializers.ValidationError({"paiement": "Le paiement ne peut pas être supérieur au coût total."})

        facture.save()

        return facture

class FactureInscritSerializer(serializers.ModelSerializer):
    details = FactureDetailsSerializer(many=True)
    cout_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = FactureInscrit
        fields = [
            'idclient', 'reduction', 'paiement', 'details', 'cout_total'
        ]

    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        reduction = validated_data.get('reduction', 0) or 0

        facture = FactureInscrit.objects.create(**validated_data)

        cout_total = 0

        for detail in details_data:
            prix_unitaire = detail.get('prix_unitaire', 0)
            quantite = detail.get('quantite', 1)
            montant_detail = prix_unitaire * quantite

            FactureDetails.objects.create(facture_inscrit=facture, **detail)

            cout_total += montant_detail

        # Application de la réduction si applicable
        cout_total = max(0, cout_total)

        # Vérifier que le paiement ne dépasse pas le coût total
        paiement = validated_data.get('paiement', 0) or 0
        if paiement > cout_total:
            raise serializers.ValidationError({"paiement": "Le paiement ne peut pas être supérieur au coût total."})

        # Mise à jour du coût total
        facture.cout_total = cout_total
        facture.save()

        return facture

class FactureDetailsSerializer(serializers.ModelSerializer):
    idmodule = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())  # ✅ Ajouté
    module_nom = serializers.CharField(source='idmodule.module', read_only=True)
    formation_nom = serializers.CharField(source='idmodule.idformation.formation', read_only=True)
    duree = serializers.DecimalField(source='idmodule.duree', max_digits=5, decimal_places=2, read_only=True)
    class Meta:
        model = FactureDetails
        fields = ['id', 'idmodule', 'quantite', 'prix_unitaire', 'module_nom', 'formation_nom', 'duree']


class FactureInscritSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactureInscrit
        fields = '__all__'