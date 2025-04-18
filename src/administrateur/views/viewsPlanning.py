from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Case, When, Q
from django.db import models
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta, date
from administrateur.models import FactureDetails, PlanningFormation, Formateur_competence
from datetime import date
from calendar import monthrange
from administrateur.models import PlanningFormation, StockPC

def liste_plannings_mensuels(request):
    mois_choisi_str = request.GET.get('mois')
    plannings = PlanningFormation.objects.all().order_by('dateFormation', 'heureDebFormation')
    mois_courant_str = None

    if mois_choisi_str:
        try:
            mois_choisi = parse_date(f'{mois_choisi_str}-01')
            if mois_choisi:
                annee = mois_choisi.year
                mois = mois_choisi.month
                debut_mois = date(annee, mois, 1)
                fin_mois = date(annee, mois, monthrange(annee, mois)[1])
                plannings = plannings.filter(dateFormation__range=(debut_mois, fin_mois))
                mois_courant_str = debut_mois.strftime('%B %Y')
            else:
                # Si la date n'est pas valide, revenir au mois courant
                today = date.today()
                debut_mois = date(today.year, today.month, 1)
                mois_courant_str = debut_mois.strftime('%B %Y')
        except ValueError:
            # Gestion d'une chaîne de mois invalide
            today = date.today()
            debut_mois = date(today.year, today.month, 1)
            mois_courant_str = debut_mois.strftime('%B %Y')
    else:
        # Afficher le mois courant par défaut
        today = date.today()
        debut_mois = date(today.year, today.month, 1)
        mois_courant_str = debut_mois.strftime('%B %Y')
        fin_mois = date(today.year, today.month, monthrange(today.year, today.month)[1])
        plannings = plannings.filter(dateFormation__range=(debut_mois, fin_mois))

    return render(request, 'admin/planning/listePlanning.html', {
        'plannings': plannings,
        'mois_courant': mois_courant_str,
    })


@login_required
def creer_planning(request, facture_detail_id):
    facture_detail = get_object_or_404(FactureDetails, id=facture_detail_id)
    formateurs = Formateur_competence.objects.filter(idmodule=facture_detail.idmodule)

    # Nombre de PC nécessaires pour cette formation
    nbr_location_pc = 0
    if facture_detail.facture_inscrit:
        nbr_location_pc = facture_detail.facture_inscrit.nbr_location_pc or 0
    elif facture_detail.facture_non_inscrit:
        nbr_location_pc = facture_detail.facture_non_inscrit.nbr_location_pc or 0

    # Stock total
    stock_pc = StockPC.objects.first()
    stock_total = stock_pc.stock if stock_pc else 0

    if request.method == 'POST':
        formateur_id = request.POST.get('formateur')
        date_formation = request.POST.get('date_formation')
        heure_debut = request.POST.get('heure_debut')
        heure_fin = request.POST.get('heure_fin')
        commentaire = request.POST.get('commentaire')

        try:
            date_formation_obj = datetime.strptime(date_formation, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Format de date invalide. Utilisez le format AAAA-MM-JJ.")
            return render(request, 'admin/planning/planning.html', {
                'facture_detail': facture_detail,
                'formateurs': formateurs,
            })

        heure_debut_obj = datetime.strptime(heure_debut, "%H:%M").time()
        heure_fin_obj = datetime.strptime(heure_fin, "%H:%M").time()

        # Vérifier les conflits de formateur avec un décalage d'1h
        conflits_formateur = PlanningFormation.objects.filter(
            idformateur=formateur_id,
            dateFormation=date_formation_obj
        ).filter(
            Q(heureDebFormation__lte=(datetime.combine(date.min, heure_fin_obj) + timedelta(minutes=59)).time()) &
            Q(heureFinFormation__gte=(datetime.combine(date.min, heure_debut_obj) - timedelta(minutes=59)).time())
        )

        if conflits_formateur.exists():
            messages.error(request, "Ce formateur a déjà un planning qui chevauche ces horaires ou ne respecte pas le décalage d'1h.")
            return render(request, 'admin/planning/planning.html', {
                'facture_detail': facture_detail,
                'formateurs': formateurs,
            })

        # Calcul des PC déjà alloués à d'autres formations au même créneau
        pcs_utilises = PlanningFormation.objects.filter(
            dateFormation=date_formation_obj
        ).filter(
            Q(heureDebFormation__lt=heure_fin_obj) &
            Q(heureFinFormation__gt=heure_debut_obj)
        ).aggregate(
            total_pcs=Sum(
                Case(
                    When(idfacturedetail__facture_inscrit__isnull=False, then='idfacturedetail__facture_inscrit__nbr_location_pc'),
                    When(idfacturedetail__facture_non_inscrit__isnull=False, then='idfacturedetail__facture_non_inscrit__nbr_location_pc'),
                    default=0,
                    output_field=models.IntegerField()
                )
            )
        )['total_pcs'] or 0

        # Calcul du stock disponible en fonction des PCs déjà alloués
        stock_disponible = stock_total - pcs_utilises

        if nbr_location_pc > stock_disponible:
            messages.error(request, f"Stock de PC insuffisant. Requis: {nbr_location_pc}, Disponible: {stock_disponible}.")
        else:
            # Créer le planning sans toucher directement au stock
            PlanningFormation.objects.create(
                idformateur_id=formateur_id,
                idmodule=facture_detail.idmodule,
                idfacturedetail=facture_detail,
                dateFormation=date_formation_obj,
                heureDebFormation=heure_debut_obj,
                heureFinFormation=heure_fin_obj,
                commentaire=commentaire,
            )
            messages.success(request, "Planning créé avec succès.")
            
    return render(request, 'admin/planning/planning.html', {
        'facture_detail': facture_detail,
        'formateurs': formateurs,
        'stock_disponible': stock_total,  # Stock total initial pour affichage
        'nbr_location_pc': nbr_location_pc,
    })
