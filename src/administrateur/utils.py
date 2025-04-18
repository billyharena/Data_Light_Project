from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404
from datetime import datetime
from administrateur.models import CustomUser, DetailAdmin
from django.db.models import Q
from datetime import datetime
from decimal import Decimal

def convert_time_to_hours(time_str):
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        return Decimal(time_obj.hour) + (Decimal(time_obj.minute) / Decimal(60))
    except ValueError:
        return None  # Handle empty or invalid time input

# Besoin de modification surtout avec la liste
def list_admin(request, permission, role_utilisateur, path, search_query, role):
    if  request.user.is_authenticated and request.user.role_utilisateur in permission:
        admin = CustomUser.objects.filter(Q(role_utilisateur=role_utilisateur.get("role"))|Q(role_utilisateur=role_utilisateur.get("super"))).order_by('id').exclude(id=request.user.id)
        if search_query:
            admin = admin.filter(
                    Q(nom__icontains=search_query) | Q(prenom__icontains=search_query)
                )
        if role:
            admin = admin.filter(role_utilisateur=role)
        return render(request, 'admin/'+ path, {'admin': admin})
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
    
def inscription_admin(request, permission, path, default_password, role_utilisateur):
    if request.user.is_authenticated and request.user.role_utilisateur in permission:
        if request.method == 'POST':
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            email = request.POST.get('email')
            date_debut = request.POST.get('date_debut')
            date_naissance = request.POST.get('date_naissance')
            adresse = request.POST.get('adresse')
            sexe = request.POST.get('sexe').lower()
            if sexe == 'h':
                sexe = 1
            elif sexe == 'f':
                sexe = 2
            role_utilisateur = role_utilisateur
            password = default_password
            if role_utilisateur == 1:
                inscrit = CustomUser.objects.create_superuser(email=email, nom=nom, prenom=prenom, password=password)
            else:
                inscrit = CustomUser.objects.create_user(email=email, nom=nom, prenom=prenom, type_utilisateur=1, role_utilisateur=role_utilisateur, password=password)
            DetailAdmin.objects.create(utilisateur=inscrit, date_debut=date_debut, date_naissance=date_naissance, sexe=sexe, adresse=adresse)
            return redirect(path.get("redirectionPost"))
    
        return render(request, 'admin/'+ path.get("redirectionGet"))
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

def modifier_admin(request, id, permission, path):
    if request.user.is_authenticated and request.user.role_utilisateur in permission:  # Vérification du rôle utilisateur
        try:
            admin = CustomUser.objects.get(id=id)  # Si l'ID n'existe pas, une exception sera levée
        except CustomUser.DoesNotExist:
            raise Http404("Utilisateur non trouvé")
        if request.method == 'POST':
            # Récupérer les valeurs du formulaire
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            email = request.POST.get('email')
            is_active = request.POST.get('is_active') == 'True'
            adresse = request.POST.get('adresse')
            contact = request.POST.get('contact')
            date_naissance = request.POST.get('date_naissance')
            date_debut = request.POST.get('date_debut')
            sexe = request.POST.get('sexe')

            # Mettre à jour l'utilisateur dans le modèle CustomUser
            admin = CustomUser.objects.get(id=id)
            admin.nom = nom
            admin.prenom = prenom
            admin.email = email
            admin.is_active = is_active
            admin.save()

            # Si un DetailAdmin existe déjà pour cet utilisateur, on met à jour les informations
            detail_admin, created = DetailAdmin.objects.update_or_create(
                utilisateur=admin,
                defaults={
                    'adresse': adresse,
                    'contact': contact,
                    'date_naissance': date_naissance,
                    'date_debut': date_debut,
                    'sexe': 1 if sexe == 'h' else 2  # 'h' pour Homme, 'f' pour Femme
                }
            )

            # Rediriger après la sauvegarde
            return redirect(path.get("redirectionPost"))

        else:
            # Si la méthode n'est pas POST, afficher le formulaire avec les informations existantes
            admin = CustomUser.objects.get(id=id)
            detail_admin = DetailAdmin.objects.filter(utilisateur__id=id).first()  # Récupérer le DetailAdmin existant
            context = {
                'admin': admin,
                'detail_admin': detail_admin  # Passer les données de DetailAdmin
            }
            return render(request, 'admin/'+ path.get("redirectionGet"), context)
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
