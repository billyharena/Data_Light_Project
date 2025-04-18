from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from django.db.models import Q
from administrateur.utils import list_admin, inscription_admin, modifier_admin
from administrateur.models import CustomUser, DetailClient
from django.http import HttpResponseForbidden, Http404
from administrateur.models import ProformaInscrit, ProformaNonInscrit, CustomUser, Module, ProformaDetails
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils.timezone import now

@login_required
def list_admins(request):
    role_utilisateur = {
        "role": 2,
        "super": 1
    }
    search = search_query = request.GET.get("search", "")
    role = request.GET.get("role", "")
    if role:
        role = 1 if role == 's' else 2
    return list_admin(request, permission=[1], role_utilisateur=role_utilisateur, path='admin/listeAdmin.html', search_query=search, role=role)
    
@login_required
def inscription_admins(request):
    paths = {
        "redirectionPost": "list_admin",
        "redirectionGet": "admin/inscrireAdmin.html"
    }
    admin = request.POST.get('admin')
    admin = 1 if admin == 's' else 2
    return inscription_admin(request=request, permission=[1], path=paths, default_password='admin', role_utilisateur=admin)

@login_required
def modifier_admins(request, id):
    paths = {
        "redirectionPost": "list_admin",
        "redirectionGet": "admin/informationAdmin.html"
    }
    return modifier_admin(request=request, id=id, permission=[1], path=paths)

@login_required
def statistiques_clients(request):
    # Récupérer les paramètres de mois et année depuis la requête GET
    mois = request.GET.get('mois', now().month)  # Mois courant par défaut
    annee = request.GET.get('annee', now().year)  # Année courante par défaut

    # Plage de mois pour le filtre
    mois_range = list(range(1, 13))  # Plage de mois de 1 à 12

    # Plage d'années (par exemple de 2020 jusqu'à l'année actuelle)
    annee_range = list(range(2020, now().year + 1))  # De 2020 à l'année actuelle

    # Filtrer par mois et année pour ProformaInscrit
    stats_inscrit = ProformaInscrit.objects.filter(
        date_creation__year=annee, date_creation__month=mois
    ).aggregate(
        total_inscrit=Sum('cout_total', filter=Q(etat=0)),
        generer_inscrit=Count('id'),
        convertit=Count('id', filter=Q(etat=1))
    )
    total_inscrit = stats_inscrit['total_inscrit'] or 0
    generer_inscrit = stats_inscrit['generer_inscrit']
    convertit_inscrit = stats_inscrit['convertit'] or 0

    # Filtrer par mois et année pour ProformaNonInscrit
    stats_non_inscrit = ProformaNonInscrit.objects.filter(
        date_creation_pf__year=annee, date_creation_pf__month=mois
    ).aggregate(
        total_non_inscrit=Sum('cout_total', filter=Q(etat=0)),
        generer_non_inscrit=Count('id'),
        convertit=Count('id', filter=Q(etat=1))
    )
    total_non_inscrit = stats_non_inscrit['total_non_inscrit'] or 0
    generer_non_inscrit = stats_non_inscrit['generer_non_inscrit']
    convertit_non_inscrit = stats_non_inscrit['convertit'] or 0

    # Calculs finaux
    somme_total = total_inscrit + total_non_inscrit
    total_generer = generer_inscrit + generer_non_inscrit
    context = {
        'total_inscrit': total_inscrit,
        'total_non_inscrit': total_non_inscrit,
        'somme_total': somme_total,
        'generer_inscrit': generer_inscrit,
        'generer_non_inscrit': generer_non_inscrit,
        'total_generer': total_generer,
        'convertit_inscrit': convertit_inscrit,
        'convertit_non_inscrit': convertit_non_inscrit,
        'mois': int(mois),
        'annee': int(annee),
        'mois_range': mois_range,
        'annee_range': annee_range,
    }

    # Rendu de la vue avec les plages d'années et de mois
    return render(request, 'admin/dashboard/dashboard.html', context)