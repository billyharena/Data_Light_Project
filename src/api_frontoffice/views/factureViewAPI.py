from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from administrateur.models.facturation import FactureInscrit
from administrateur.models import DetailClient, PlanningFormation
from ..serializers.factureSerializer import FactureNonInscritSerializer, FactureInscritSerializer, FactureDetailsSerializer

class FactureNonInscritAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = FactureNonInscritSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FactureInscritAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = FactureInscritSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ListeFactureInscritAPIView(APIView):
    def get(self, request, *args, **kwargs):
        factures = FactureInscrit.objects.filter(idclient=request.user)
        serializer = FactureInscritSerializer(factures, many=True)
        return Response(serializer.data)
    

class FactureDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, facture_id):
        """
        Récupère les détails d'une facture spécifique avec ses modules associés.
        """
        facture = get_object_or_404(FactureInscrit, id=facture_id, idclient=request.user)
        facture_serializer = FactureInscritSerializer(facture)
        
        # Récupérer les détails liés à cette facture
        details = facture.details.all()
        details_data = []
        
        for detail in details:
            est_plannifie = PlanningFormation.objects.filter(
                idmodule=detail.idmodule,  # Correction ici
                idfacturedetail=detail.id
            ).exists()

            
            detail_data = FactureDetailsSerializer(detail).data
            detail_data["estPlannifie"] = est_plannifie
            details_data.append(detail_data)

        client = facture.idclient
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
            "facture": facture_serializer.data,
            "details": details_data,
            "client": client_info
        }, status=status.HTTP_200_OK)
