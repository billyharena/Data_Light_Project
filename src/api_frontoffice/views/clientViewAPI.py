from django.contrib.auth import authenticate
from rest_framework import status
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from administrateur.models import CustomUser, DetailClient
from ..serializers import ClientRegisterSerializer, LoginSerializer, ClientProfileSerializer, ClientProfileUpdateSerializer

# Inscription client
class ClientRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("📩 Données reçues :", request.data)  # Log des données envoyées
        
        serializer = ClientRegisterSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            
            try:
                with transaction.atomic():  # Démarrer une transaction atomique
                    # Création de l'utilisateur
                    user = CustomUser.objects.create_user(
                        email=validated_data['email'],
                        nom=validated_data['nom'],
                        prenom=validated_data['prenom'],
                        type_utilisateur=2,
                        password=validated_data['password'],
                        role_utilisateur=4 if validated_data['type_client'] == 1 else 5
                    )

                    # Création des détails client
                    detail_client = DetailClient.objects.create(
                        utilisateur=user,
                        sexe=validated_data.get('sexe'),
                        type_client=validated_data['type_client'],
                        raison_social=validated_data.get('raison_social', None),
                        contact_entreprise=validated_data.get('contact_entreprise', None),
                        date_creation_entreprise=validated_data.get('date_creation_entreprise', None),
                    )

                    # Création du token d'authentification
                    token, created = Token.objects.get_or_create(user=user)
                
                return Response({
                    "token": token.key,
                    "email": user.email,
                    "type_client": detail_client.type_client,
                    "message": "Inscription réussie !"
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                print("❌ Erreur lors de l'enregistrement :", str(e))  # Log des erreurs
                return Response({"error": "Une erreur est survenue, veuillez réessayer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print("❌ Erreur de validation :", serializer.errors)  # Log des erreurs
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Connexion client
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({"token": token.key, "email": user.email}, status=status.HTTP_200_OK)
            return Response({"error": "Identifiants invalides"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Déconnexion client
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Supprimer le token de l'utilisateur authentifié
            Token.objects.filter(user=request.user).delete()
            return Response({"message": "Déconnexion réussie."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Modification des détails du client
# class ClientUpdateAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def put(self, request):
#         try:
#             client_details = DetailClient.objects.get(utilisateur=request.user)
#             serializer = ClientUpdateSerializer(client_details, data=request.data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response({"message": "Détails du client mis à jour avec succès"}, status=status.HTTP_200_OK)
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#         except DetailClient.DoesNotExist:
#             return Response({"error": "Détails du client introuvables"}, status=status.HTTP_404_NOT_FOUND)

class ClientProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client_details = DetailClient.objects.get(utilisateur=request.user)
            serializer = ClientProfileSerializer(client_details)

            user_data = {
                "nom": request.user.nom,
                "prenom": request.user.prenom,
                "email": request.user.email,
            }

            return Response({**user_data, **serializer.data}, status=status.HTTP_200_OK)
        except DetailClient.DoesNotExist:
            return Response({"error": "Détails du client introuvables."}, status=status.HTTP_404_NOT_FOUND)

class ClientProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """Met à jour les informations du client"""
        try:
            client_details = DetailClient.objects.get(utilisateur=request.user)
            serializer = ClientProfileUpdateSerializer(client_details, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Profil mis à jour avec succès."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except DetailClient.DoesNotExist:
            return Response({"error": "Détails du client introuvables."}, status=status.HTTP_404_NOT_FOUND)