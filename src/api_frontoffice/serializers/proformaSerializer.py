from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
from administrateur.models import ProformaNonInscrit, ProformaDetails, ProformaInscrit
from administrateur.models import Module
from administrateur.models.facturation.baseFacturation import Extra

class ProformaDetailsSerializer(serializers.ModelSerializer):
    idmodule = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())
    module_nom = serializers.CharField(source='idmodule.module', read_only=True)
    formation_nom = serializers.CharField(source='idmodule.idformation.formation', read_only=True)
    duree = serializers.DecimalField(source='idmodule.duree', max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = ProformaDetails
        fields = ['id', 'idmodule', 'quantite', 'prix_unitaire', 'module_nom', 'formation_nom', 'duree']

    def validate_quantite(self, value):
        if value < 1:
            raise serializers.ValidationError("La quantité doit être au moins 1.")
        return value


class ProformaNonInscritSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaNonInscrit
        fields = '__all__'

class CreateProformaNonInscritSerializer(serializers.Serializer):
    client = ProformaNonInscritSerializer()
    details = ProformaDetailsSerializer(many=True)

    def create(self, validated_data):
        try:
            with transaction.atomic():
                # 🔍 Extraction des données du client
                client_data = validated_data.pop('client')

                # ✅ Création du proforma
                proforma = ProformaNonInscrit.objects.create(**client_data)

                # 🔄 Extraction des détails du proforma
                details_data = validated_data.pop('details')
                total = 0
                details_instances = []

                for detail in details_data:
                    module_id = detail['idmodule'].id

                    # ✅ Vérification si le module existe
                    try:
                        module = Module.objects.get(id=module_id)
                    except ObjectDoesNotExist:
                        raise serializers.ValidationError(f"Le module avec l'ID {module_id} n'existe pas.")

                    # ✅ Vérification de la quantité
                    quantite = detail['quantite']
                    if quantite <= 0:
                        raise serializers.ValidationError("La quantité doit être supérieure à 0.")

                    # Calcul du total
                    total += module.prix * quantite

                    # Création des détails mais sans sauvegarde immédiate
                    details_instances.append(ProformaDetails(
                        proforma_non_inscrit=proforma,
                        idmodule=module,
                        quantite=quantite,
                        prix_unitaire=module.prix
                    ))

                # ✅ Appliquer une réduction si plus de 3 modules sont demandés
                # if len(details_data) > 3:
                #     reduction = total * 0.1  # Réduction de 10%
                #     total -= reduction
                #     proforma.reduction = reduction

                # ✅ Mise à jour du coût total
                proforma.cout_total = total
                proforma.save()

                # 🔄 Insérer tous les détails en une seule requête (optimisation)
                ProformaDetails.objects.bulk_create(details_instances)

            return proforma

        except serializers.ValidationError as e:
            raise e  # Garder les messages d'erreur spécifiques
        except Exception as e:
            raise serializers.ValidationError(f"Erreur lors de la création du proforma : {str(e)}")


class ProformaInscritSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProformaInscrit
        fields = '__all__'

class CreateProformaInscritSerializer(serializers.Serializer):
    details = ProformaDetailsSerializer(many=True)

    def create(self, validated_data):
        request = self.context.get('request')
        client = request.user  # L'utilisateur inscrit qui fait la demande

        try:
            with transaction.atomic():
                # ✅ Création du ProformaInscrit
                proforma = ProformaInscrit.objects.create(
                    idclient=client,
                    id_createur=client.id,  # L'id du client devient id_createur
                )

                # ✅ Extraction des détails du proforma
                details_data = validated_data.pop('details', [])
                total = Decimal('0.0')
                details_instances = []

                for detail in details_data:
                    module_id = detail['idmodule'].id

                    # ✅ Vérification si le module existe
                    try:
                        module = Module.objects.get(id=module_id)
                    except ObjectDoesNotExist:
                        raise serializers.ValidationError(f"Le module avec l'ID {module_id} n'existe pas.")

                    # ✅ Vérification de la quantité
                    quantite = detail['quantite']
                    if quantite <= 0:
                        raise serializers.ValidationError("La quantité doit être supérieure à 0.")

                    # ✅ Assurer que le prix est bien un Decimal
                    prix_unitaire = Decimal(str(module.prix))  # Conversion sécurisée

                    total += prix_unitaire * Decimal(quantite)

                    # Création des détails mais sans sauvegarde immédiate
                    details_instances.append(ProformaDetails(
                        proforma_inscrit=proforma,
                        idmodule=module,
                        quantite=quantite,
                        prix_unitaire=prix_unitaire
                    ))

                # ✅ Appliquer une réduction si plus de 3 modules sont demandés
                if len(details_data) > 3:
                    reduction = total * Decimal('0.1')  # Réduction de 10%
                    total -= reduction
                    proforma.reduction = reduction
                else:
                    proforma.reduction = Decimal('0.0')
                # ✅ Mise à jour du coût total
                proforma.cout_total = total
                proforma.save()

                # ✅ Insérer tous les détails en une seule requête
                ProformaDetails.objects.bulk_create(details_instances)

            return proforma

        except serializers.ValidationError as e:
            raise e  # Garde les messages d'erreur spécifiques
        except Exception as e:
            raise serializers.ValidationError(f"Erreur lors de la création du proforma : {str(e)}")
