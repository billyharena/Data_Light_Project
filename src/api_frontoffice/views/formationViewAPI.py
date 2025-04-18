from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from administrateur.models.formationModel import Formation, Module
from ..serializers.formationSerializer import FormationSerializer, ModuleSerializer

class FormationList(APIView):
    def get(self, request):
        formations = Formation.objects.all()
        serializer = FormationSerializer(formations, many=True)
        return Response(serializer.data)

class FormationDetail(APIView):
    def get(self, request, formation_id):
        formation = Formation.objects.filter(id=formation_id).first()
        if not formation:
            return Response(
                {"message": "Aucune formation de ce genre"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = FormationSerializer(formation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ModuleList(APIView):
    def get(self, request, formation_id, *args, **kwargs):
        modules = Module.objects.filter(idformation_id=formation_id)

        if not modules.exists():
            return Response(
                {"message": "Aucun module pour cette formation"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)