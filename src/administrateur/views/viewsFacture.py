from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404
from administrateur.models import ProformaInscrit, ProformaNonInscrit, CustomUser, Module, ProformaDetails, FactureDetails, FactureInscrit, FactureNonInscrit
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

@login_required
def list_facture(request):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        # Récupérer les paramètres de filtrage depuis la requête GET
        search_query = request.GET.get("search", "")
        date_start = request.GET.get("date_start", "")
        date_end = request.GET.get("date_end", "")
        num = request.GET.get("num", "")

        # Filtre pour les proformas inscrits
        facture_inscrit = FactureInscrit.objects.all()
        facture_non_inscrit = FactureNonInscrit.objects.all()

        if search_query:
            facture_inscrit = facture_inscrit.filter(
                Q(idclient__nom__icontains=search_query) | Q(idclient__prenom__icontains=search_query)
            )
            facture_non_inscrit = facture_non_inscrit.filter(
                Q(nom__icontains=search_query) | Q(prenom__icontains=search_query) | Q(nom_entreprise__icontains=search_query)
            )

        if num :
            facture_inscrit = facture_inscrit.filter(id=int(num))
            facture_non_inscrit = facture_non_inscrit.filter(id=int(num))

        if date_start:
            facture_inscrit = facture_inscrit.filter(date_creation__gte=date_start)
            facture_non_inscrit = facture_non_inscrit.filter(date_creation_pf__gte=date_start)

        if date_end:
            facture_inscrit = facture_inscrit.filter(date_creation__lte=date_end)
            facture_non_inscrit = facture_non_inscrit.filter(date_creation_pf__lte=date_end)

        return render(request, "admin/facturation/facture/listeFacture.html", {
            "facture_inscrit": facture_inscrit,
            "facture_non_inscrit": facture_non_inscrit,
            "search_query": search_query,
            "date_start": date_start,
            "date_end": date_end,
        })
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

# Proforma inscrit -> Facture inscrit
@login_required
def convertir_proforma_en_facture(request, id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        # Récupérer la proforma
        proforma = get_object_or_404(ProformaInscrit, id=id)
        client = get_object_or_404(CustomUser, id=proforma.idclient.id)
        try:
            with transaction.atomic():
                # Créer une facture inscrite à partir de la proforma
                facture = FactureInscrit.objects.create(
                    id_createur=proforma.id_createur,
                    lieu_formation=proforma.lieu_formation,
                    nbr_location_pc=proforma.nbr_location_pc,
                    pu_pc=proforma.pu_pc,
                    nbr_frais_transport=proforma.nbr_frais_transport,
                    pu_transport=proforma.pu_transport,
                    nbr_frais_restauration=proforma.nbr_frais_restauration,
                    pu_restauration=proforma.pu_restauration,
                    hebergement=proforma.hebergement,
                    pu_hebergement=proforma.pu_hebergement,
                    date_creation=proforma.date_creation,
                    cout_total=proforma.cout_total,
                    reduction=proforma.reduction,
                    idclient=client,
                )
                proforma.facture = facture.id
                proforma.etat = 1
                proforma.save()
                # Copier les détails de la proforma vers les détails de la facture
                for detail in proforma.details.all():
                    FactureDetails.objects.create(
                        idmodule=detail.idmodule,
                        facture_inscrit=facture,
                        prix_unitaire=detail.prix_unitaire,
                        quantite=detail.quantite,
                    )

            # Ajouter un message de succès
            messages.success(request, "La proforma a été convertie en facture avec succès.")
            return redirect('list_facture')

        except Exception as e:
            # En cas d'erreur, afficher un message
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('modification_proforma_inscrit', id=proforma.id)
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
    
@login_required
def inscrire_facture_non_inscrit(request, id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        # Récupérer le proforma non inscrit
        proforma = get_object_or_404(ProformaNonInscrit, id=id)

        try:
        # Créer une facture à partir du proforma
            facture = FactureNonInscrit.objects.create(
                id_createur = request.user.id,
                nom=proforma.nom,
                prenom=proforma.prenom,
                nom_entreprise=proforma.nom_entreprise,
                adresse_entreprise=proforma.adresse_entreprise,
                contact=proforma.contact,
                nif=proforma.nif,
                stat=proforma.stat,
                rcs=proforma.rcs,
                cnaps=proforma.cnaps,
                lieu_formation=proforma.lieu_formation,
                nbr_location_pc=proforma.nbr_location_pc,
                pu_pc=proforma.pu_pc,
                nbr_frais_transport=proforma.nbr_frais_transport,
                pu_transport=proforma.pu_transport,
                nbr_frais_restauration=proforma.nbr_frais_restauration,
                pu_restauration=proforma.pu_restauration,
                hebergement=proforma.hebergement,
                pu_hebergement=proforma.pu_hebergement,
                cout_total=proforma.cout_total,
            )
            proforma.facture_non_inscrit = facture.id
            proforma.etat = 1
            proforma.save()
            # Copier les détails du proforma vers la facture
            proforma_details = ProformaDetails.objects.filter(proforma_non_inscrit=proforma)
            for detail in proforma_details:
                FactureDetails.objects.create(
                    idmodule=detail.idmodule,
                    facture_non_inscrit=facture,
                    quantite=detail.quantite,
                    duree_seance=detail.duree_seance,
                    nbr_seance=detail.nbr_seance,
                    prix_unitaire=detail.prix_unitaire,
                )

            messages.success(request, "La proforma a été convertie en facture avec succès.")
            return redirect('list_facture')

        except Exception as e:
            # En cas d'erreur, afficher un message
            messages.error(request, f"Une erreur s'est produite : {str(e)}")
            return redirect('modification_proforma_non_inscrit', id=proforma.id)
    else:
        return JsonResponse({"error": "Vous n'avez pas l'autorisation d'accéder à cette page."}, status=403)
    
@login_required
def voir_facture_non_inscrit(request, id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        facture = get_object_or_404(FactureNonInscrit, id=id)
        paiement_f = facture.paiement or Decimal(0)

        if request.method == "POST":
            paiement = request.POST.get('paiement')
            paiement = Decimal(paiement) if paiement else Decimal(0)
            nouveau_paiement = paiement_f + paiement  # Calculer le nouveau paiement total

            try:
                # Mettre à jour le paiement dans l'objet facture
                facture.paiement = nouveau_paiement
                facture.clean()  # Valider avant la sauvegarde
                facture.save()

                messages.success(request, "Paiement effectué avec succès!")
                paiement_f = nouveau_paiement  # Mettre à jour paiement_f pour refléter les changements
            except ValidationError as e:
                # Gérer les erreurs de validation
                messages.error(request, e.message_dict.get('paiement', "Erreur dans les données."))

        # Calculer le reste à payer après la mise à jour
        reste_payer = facture.cout_total - paiement_f

        return render(request, 'admin/facturation/facture/voirFactureNonInscrit.html', {
            'facture_non_inscrit': facture,
            'facture_details': facture.details.all(),
            'modules': Module.objects.all(),
            'reste_payer': reste_payer
        })
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")


@login_required
def voir_facture_inscrit(request, id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        facture = get_object_or_404(FactureInscrit, id=id)
        paiement_f = facture.paiement or Decimal(0)

        if request.method == "POST":
            paiement = request.POST.get('paiement')
            paiement = Decimal(paiement) if paiement else Decimal(0)
            nouveau_paiement = paiement_f + paiement  # Calculer le nouveau paiement total

            try:
                # Mettre à jour le paiement dans l'objet facture
                facture.paiement = nouveau_paiement
                facture.clean()  # Valider avant la sauvegarde
                facture.save()

                messages.success(request, "Paiement effectué avec succès!")
                paiement_f = nouveau_paiement  # Mettre à jour paiement_f pour refléter les changements
            except ValidationError as e:
                # Gérer les erreurs de validation
                messages.error(request, e.message_dict.get('paiement', "Erreur dans les données."))

        # Calculer le reste à payer après la mise à jour
        reste_payer = facture.cout_total - paiement_f

        return render(request, 'admin/facturation/facture/voirFactureInscrit.html', {
            'facture_inscrit': facture,
            'facture_details': facture.details.all(),
            'modules': Module.objects.all(),
            'reste_payer': reste_payer
        })
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
