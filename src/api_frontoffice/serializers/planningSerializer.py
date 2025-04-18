from rest_framework import serializers
from administrateur.models import CustomUser, PlanningFormation

class PlanningFormationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanningFormation
        fields = ['dateFormation', 'heureDebFormation', 'heureFinFormation']

class DisponibiliteSerializer(serializers.Serializer):
    idformateur = serializers.IntegerField()
    duree_module = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    disponibilites = PlanningFormationSerializer(many=True)

