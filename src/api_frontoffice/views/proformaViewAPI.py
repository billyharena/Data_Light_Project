from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q
from administrateur.models import ProformaInscrit, ProformaDetails, FactureInscrit, FactureDetails, DetailClient
from ..serializers import ProformaNonInscritSerializer, CreateProformaInscritSerializer, CreateProformaNonInscritSerializer, ProformaInscritSerializer, ProformaDetailsSerializer

class CreateProformaNonInscritAPIView(APIView):
    def post(self, request):
        serializer = CreateProformaNonInscritSerializer(data=request.data)
        if serializer.is_valid():
            proforma = serializer.save()
            return Response(
                {"message": "Proforma créé avec succès", "id": proforma.id}, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateProformaInscritAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # Seuls les utilisateurs connectés peuvent faire la demande

    def post(self, request):
        serializer = CreateProformaInscritSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            proforma = serializer.save()
            return Response(
                {"message": "Proforma inscrit créé avec succès", "id": proforma.id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ListeProformasInscritAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        proformas = ProformaInscrit.objects.filter(Q(idclient=request.user) & Q(etat=0))
        serializer = ProformaInscritSerializer(proformas, many=True)
        return Response(serializer.data)
    
class ProformaDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, proforma_id):
        """
        Récupère les détails d'un proforma spécifique avec ses modules associés et les infos du client.
        """
        proforma = get_object_or_404(ProformaInscrit, id=proforma_id, idclient=request.user)
        proforma_serializer = ProformaInscritSerializer(proforma)

        # Récupérer les détails liés à ce proforma
        details = proforma.details.all()
        details_serializer = ProformaDetailsSerializer(details, many=True)

        # Récupérer les informations du client
        client = proforma.idclient
        client_details = get_object_or_404(DetailClient, utilisateur=client)

        client_info = {
            "nom": client.nom,
            "prenom": client.prenom,
            "adresse": client_details.adresse,
            "type_client": client_details.type_client,
            "raison_social": client_details.raison_social if client_details.type_client == 2 else None,
            "nif": client_details.nif if client_details.type_client == 2 else None,
            "stat": client_details.stat if client_details.type_client == 2 else None,
            "rcs": client_details.rcs if client_details.type_client == 2 else None,
        }

        return Response({
            "proforma": proforma_serializer.data,
            "details": details_serializer.data,
            "client": client_info
        }, status=status.HTTP_200_OK)

    
class ProformaDetailsDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, proforma_id, detail_id):
        """
        Supprime un module du proforma, met à jour le coût total et ajuste la réduction dynamiquement.
        """
        proforma_detail = get_object_or_404(ProformaDetails, id=detail_id, proforma_inscrit_id=proforma_id)
        proforma = proforma_detail.proforma_inscrit  # Récupération du proforma associé

        # Vérifie si le proforma appartient à l'utilisateur connecté
        if proforma.idclient != request.user:
            return Response({"error": "Vous n'avez pas l'autorisation de supprimer ce module."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            with transaction.atomic():
                # Supprimer le module
                proforma_detail.delete()

                # Récupérer les modules restants
                modules_restants = ProformaDetails.objects.filter(proforma_inscrit=proforma)

                # Recalcul du coût total après suppression
                nouveau_cout_total = sum(int(detail.quantite) * float(detail.prix_unitaire) for detail in modules_restants)

                # Mettre à jour la réduction si nécessaire
                if modules_restants.count() > 3:
                    # Appliquer une réduction de 10% (par exemple)
                    nouvelle_reduction = nouveau_cout_total * 0.1  
                else:
                    nouvelle_reduction = 0  # Plus de réduction si 3 modules ou moins

                # Mise à jour du proforma
                proforma.reduction = nouvelle_reduction
                proforma.cout_total = max(nouveau_cout_total - nouvelle_reduction, 0)
                proforma.save()

            return Response({
                "message": "Module supprimé avec succès.",
                "nouveau_cout_total": proforma.cout_total,
                "nouvelle_reduction": proforma.reduction
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Erreur lors de la suppression d'un module: {str(e)}")  # Debug
            return Response({"error": f"Erreur lors de la suppression : {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProformaViewSet(viewsets.ModelViewSet):
    queryset = ProformaInscrit.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, pk=None):
        """Supprime un proforma et ses détails associés."""
        proforma = get_object_or_404(ProformaInscrit, pk=pk, idclient=request.user)

        try:
            with transaction.atomic():
                # Supprime les détails associés
                ProformaDetails.objects.filter(proforma_inscrit=proforma).delete()
                
                # Supprime le proforma
                proforma.delete()

            return Response({"message": "Proforma supprimé avec succès."}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"error": f"Erreur lors de la suppression : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ConvertProformaToFacture(APIView):
    """
    API pour convertir un Proforma en Facture.
    """
    def post(self, request, proforma_id):
        # Vérifie si le proforma existe
        proforma = get_object_or_404(ProformaInscrit, id=proforma_id)
        proforma_details = ProformaDetails.objects.filter(proforma_inscrit_id=proforma_id)  # ✅ Correction ici

        # Créer la facture
        facture = FactureInscrit.objects.create(
            idclient=proforma.idclient,
            cout_total=proforma.cout_total,
            reduction=proforma.reduction,
            paiement=0  # Facture en "Non Payé" car c'est un bon de commande
        )

        # Copier les détails du proforma vers facture details
        for detail in proforma_details:
            FactureDetails.objects.create(
                facture_inscrit=facture,
                idmodule=detail.idmodule,
                quantite=detail.quantite,
                prix_unitaire=detail.prix_unitaire
            )

        # 🔹 Modifier l'état du proforma et enregistrer la facture associée
        proforma.etat = 1  # ✅ Marque le proforma comme converti
        proforma.facture = facture.id  # ✅ Associe la facture au proforma
        proforma.save()  # 🔹 Sauvegarde les modifications

        return Response(
            {"message": "Facture créée avec succès", "facture_id": facture.id},
            status=status.HTTP_201_CREATED
        )

