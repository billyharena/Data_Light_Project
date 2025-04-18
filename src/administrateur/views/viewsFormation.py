from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404
from administrateur.models import Formation, Module
from django.core.exceptions import ValidationError
from django.db.models import Q

@login_required
def list_formation(request):
    if  request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        formation = Formation.objects.all()
        return render(request, 'admin/formation/listeFormation.html', {'formation': formation})
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
    
@login_required
def inscription_formation(request):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        if request.method == 'POST':
            formation = request.POST.get('formation')
            img = request.FILES.get('img')
            description = request.POST.get('description')
            Formation.objects.create(formation=formation, img=img, descriptions=description)
            return redirect("list_formation")
    
        return render(request, 'admin/formation/ajoutFormation.html')
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
    
@login_required
def modifier_formation(request, id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        try:
            formation = Formation.objects.get(id=id)
        except Formation.DoesNotExist:
            raise Http404("Formation non trouvée")

        if request.method == 'POST':
            new_nom = request.POST.get('formation')  # Nouveau nom de la formation
            new_description = request.POST.get('description')
            new_img = request.FILES.get('img')

            # Mettre à jour les champs sans écraser l'objet formation
            formation.formation = new_nom
            formation.descriptions = new_description

            if new_img:  # Vérifier si une nouvelle image a été envoyée
                formation.img = new_img

            formation.save()  # Sauvegarde en base de données

            return redirect('list_formation')

        return render(request, 'admin/formation/informationFormation.html', {
            'formation': formation,
        })

    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

@login_required
def list_module(request):
    if  request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        query_search = request.GET.get('search', '')
        if query_search:
            module = Module.objects.filter(
                Q(module__icontains=query_search) | Q(idformation__formation__icontains=query_search)
            )
        else:
            module = Module.objects.all().order_by('idformation')
        return render(request, 'admin/formation/module/listeModule.html', {'module': module})
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
    
@login_required
def inscription_module(request):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        if request.method == 'POST':
            formation_id = request.POST.get('formation')
            formation = get_object_or_404(Formation, id=int(formation_id))
            module = request.POST.get('module')
            img = request.FILES.get('img')
            description = request.POST.get('description')
            duree = request.POST.get('duree')
            prix = request.POST.get('prix')

            # Création de l'objet mais sans le sauvegarder en base de données
            module = Module(
                idformation=formation,
                module=module,
                img=img,
                descriptions=description,
                duree=duree,
                prix=prix
            )

            try:
                module.full_clean()  # Applique la méthode `clean()` et valide les champs
                module.save()  # Sauvegarde seulement si la validation passe
                return redirect("list_module")
            except ValidationError as e:
                return render(request, 'admin/formation/module/ajoutModule.html', {
                    "formation": Formation.objects.all(),
                    "errors": e.message_dict  # Envoie les erreurs au template
                })

        return render(request, 'admin/formation/module/ajoutModule.html', {"formation": Formation.objects.all()})
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

@login_required
def modifier_module(request, id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        try:
            module = Module.objects.get(id=id)
        except Formation.DoesNotExist:
            raise Http404("Module non trouvée")

        if request.method == 'POST':
            new_module_name = request.POST.get('module')
            new_description = request.POST.get('description')
            new_img = request.FILES.get('img')
            new_price = request.POST.get('prix')
            new_duree = request.POST.get('duree')
            new_formation_id = request.POST.get('formation') # Récupérer l'ID de la formation sélectionnée

            module.module = new_module_name
            module.descriptions = new_description
            module.prix = new_price
            module.duree = new_duree

            try:
                new_formation = Formation.objects.get(id=new_formation_id)
                module.idformation = new_formation
            except Formation.DoesNotExist:
                # Gérer le cas où la formation sélectionnée n'existe pas (peu probable)
                pass

            if new_img:
                module.img = new_img
            try:
                module.full_clean()
                module.save()
            except ValidationError as e:
                formations = Formation.objects.all() # Récupérer TOUTES les formations
                return render(request, 'admin/formation/module/informationModule.html', {
                    'module': module,
                    'formations': formations, # Utiliser la clé 'formations' (avec un 's')
                    "errors": e.message_dict
                })
            return redirect('list_module')

        formations = Formation.objects.all() # Récupérer TOUTES les formations
        return render(request, 'admin/formation/module/informationModule.html', {
            'module': module,
            'formations': formations # Utiliser la clé 'formations' (avec un 's')
        })

    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")