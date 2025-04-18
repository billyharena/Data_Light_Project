from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404
from administrateur.models import CustomUser, DetailClient
from django.db.models import Q

@login_required
def list_client(request):
    if  request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        search = search_query = request.GET.get("search", "")
        role = request.GET.get("role", "")
        if role:
            role = 4 if role == 'p' else 5
        admin = admin = CustomUser.objects.filter(type_utilisateur=2).order_by('role_utilisateur')
        if search_query:
            admin = admin.filter(
                    Q(nom__icontains=search_query) | Q(prenom__icontains=search_query)
                )
        if role:
            admin = admin.filter(role_utilisateur=role)
        return render(request, 'admin/client/listeClient.html', {'admin': admin})
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

@login_required
def modifier_client(request, id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:  # Vérification du rôle utilisateur
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
            role_utilisateur = request.POST.get('role_utilisateur')
            sexe = 1 if request.POST.get('sexe') == 'h' else 2
            type_client = 1 if role_utilisateur == 'p' else 2
            contact = request.POST.get('contact')
            cin = request.POST.get('cin')
            nif = request.POST.get('nif') or None
            stat = request.POST.get('stat') or None
            rcs = request.POST.get('rcs') or None
            cnaps = request.POST.get('num_cnaps') or None
            contact_entreprise = request.POST.get('contact_entreprise')
            raison_social = request.POST.get('raison_social')
            date_creation_entreprise = request.POST.get('date_creation_entreprise') if request.POST.get('date_creation_entreprise') else None
            
            adresse = request.POST.get('adresse')
            # Mettre à jour l'utilisateur dans le modèle CustomUser
            admin = CustomUser.objects.get(id=id)
            admin.nom = nom
            admin.prenom = prenom
            admin.email = email
            admin.is_active = is_active
            admin.role_utilisateur = 4 if role_utilisateur == 'p' else 5
            admin.save()

            # Mettre à jour les informations du client dans le modèle DetailClient
            detail_client, created = DetailClient.objects.update_or_create(
                utilisateur=admin,
                defaults={
                    'adresse': adresse,
                    'sexe': sexe,
                    'contact': contact,
                    'type_client': type_client,
                    'cin': cin,
                    'nif': nif,
                    'stat': stat,
                    'rcs': rcs,
                    'num_cnaps': cnaps,
                    'contact_entreprise': contact_entreprise,
                    'raison_social': raison_social,
                    'date_creation_entreprise': date_creation_entreprise
                }
            )
            # Rediriger après la sauvegarde
            return redirect("list_client")

        else:
            # Si la méthode n'est pas POST, afficher le formulaire avec les informations existantes
            admin = CustomUser.objects.get(id=id)
            detail_client = DetailClient.objects.filter(utilisateur__id=id).first()
            context = {
                'admin': admin,
                'detail_client': detail_client
            }
            return render(request, 'admin/client/informationClient.html', context)
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

    
@login_required
def inscription_client(request):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        if request.method == 'POST':
            # Récupération des données de la requête
            nom = request.POST.get('nom')
            prenom = request.POST.get('prenom')
            email = request.POST.get('email')
            adresse = request.POST.get('adresse')
            sexe = request.POST.get('sexe').lower()
            sexe = 1 if sexe == 'h' else 2
            role_utilisateur = 4 if request.POST.get('role_utilisateur') == 'p' else 5
            type_client = 1 if role_utilisateur == 4 else 2
            password = "client"

            # Création du nouvel utilisateur
            inscrit = CustomUser.objects.create_user(
                email=email,
                nom=nom,
                prenom=prenom,
                type_utilisateur=2,
                role_utilisateur=role_utilisateur,
                password=password
            )

            # Si le type de client est particulier
            if role_utilisateur == 4:  # Particulier
                contact = request.POST.get('contact')
                cin = request.POST.get('cin')
                DetailClient.objects.create(
                    utilisateur=inscrit,
                    sexe=sexe,
                    type_client=type_client,
                    contact=contact,
                    cin=cin
                )
            # Si le type de client est entreprise
            else:  # Entreprise
                raison_social = request.POST.get('raison_social')
                contact_entreprise = request.POST.get('contact_entreprise')
                date_creation_entreprise = request.POST.get('date_creation_entreprise')
                nif = request.POST.get('nif')
                stat = request.POST.get('stat')
                rcs = request.POST.get('rcs')
                num_cnaps = request.POST.get('num_cnaps')
                effectif = int(request.POST.get('effectif'))
                DetailClient.objects.create(
                    utilisateur=inscrit,
                    sexe=sexe,
                    adresse=adresse,
                    type_client=type_client,
                    raison_social=raison_social,
                    contact_entreprise=contact_entreprise,
                    date_creation_entreprise=date_creation_entreprise,
                    nif=nif,
                    stat=stat,
                    rcs=rcs,
                    num_cnaps=num_cnaps,
                    effectif=effectif
                )

            return redirect("list_client")
    
        return render(request, 'admin/client/inscrireClient.html')
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")