from rest_framework import serializers

from administrateur.models.formationModel import Formation, Module

class FormationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Formation
        fields = '__all__'

class ModuleSerializer(serializers.ModelSerializer):
    idformation = serializers.StringRelatedField()

    class Meta:
        model = Module
        fields = '__all__'