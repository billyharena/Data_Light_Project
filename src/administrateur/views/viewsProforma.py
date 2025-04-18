from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404
from administrateur.models import ProformaInscrit, ProformaNonInscrit, CustomUser, Module, ProformaDetails
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from administrateur.models import Extra
import math
from administrateur.utils import convert_time_to_hours

@login_required
def list_proforma(request):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        # Récupérer les paramètres de filtrage depuis la requête GET
        search_query = request.GET.get("search", "")
        date_start = request.GET.get("date_start", "")
        date_end = request.GET.get("date_end", "")
        num = request.GET.get("num", "")

        # Filtre pour les proformas inscrits
        proforma_inscrit = ProformaInscrit.objects.filter(etat=0)
        proforma_non_inscrit = ProformaNonInscrit.objects.filter(etat=0)

        if search_query:
            proforma_inscrit = proforma_inscrit.filter(
                Q(idclient__nom__icontains=search_query) | Q(idclient__prenom__icontains=search_query)
            )
            proforma_non_inscrit = proforma_non_inscrit.filter(
                Q(nom__icontains=search_query) | Q(prenom__icontains=search_query) | Q(nom_entreprise__icontains=search_query)
            )

        if num :
            proforma_inscrit = proforma_inscrit.filter(id=int(num))
            proforma_non_inscrit = proforma_non_inscrit.filter(id=int(num))

        if date_start:
            proforma_inscrit = proforma_inscrit.filter(date_creation__gte=date_start)
            proforma_non_inscrit = proforma_non_inscrit.filter(date_creation_pf__gte=date_start)

        if date_end:
            proforma_inscrit = proforma_inscrit.filter(date_creation__lte=date_end)
            proforma_non_inscrit = proforma_non_inscrit.filter(date_creation_pf__lte=date_end)

        return render(request, "admin/facturation/proforma/listeProforma.html", {
            "proforma_inscrit": proforma_inscrit,
            "proforma_non_inscrit": proforma_non_inscrit,
            "search_query": search_query,
            "date_start": date_start,
            "date_end": date_end,
        })
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

@login_required
def supprimer_proforma_detail(request, detail_id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        try:
            # Récupérer le détail
            detail = get_object_or_404(ProformaDetails, id=detail_id)

            # Identifier si le détail appartient à un ProformaInscrit ou ProformaNonInscrit
            if detail.proforma_inscrit:
                proforma = detail.proforma_inscrit
            elif detail.proforma_non_inscrit:
                proforma = detail.proforma_non_inscrit
            else:
                return JsonResponse({"error": "Le détail ne correspond à aucun proforma."}, status=400)

            # Mise à jour du coût total avant suppression
            proforma.cout_total -= detail.quantite * detail.prix_unitaire
            proforma.save()

            # Supprimer le détail
            detail.delete()

            # Rediriger vers la bonne vue de modification
            if detail.proforma_inscrit:
                return redirect('modification_proforma_inscrit', id=proforma.id)
            else:
                return redirect('modification_proforma_non_inscrit', id=proforma.id)

        except Exception as e:
            # Gérer les erreurs éventuelles
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

def get_extra_details(extra):
    details_extra = Extra.objects.filter(details=extra)
    return {
        'pc_pu': details_extra.filter(motif=2).first().prix if details_extra.filter(motif=2).exists() else 0,
        'transport_pu': details_extra.filter(motif=1).first().prix if details_extra.filter(motif=1).exists() else 0,
        'restauration_pu': details_extra.filter(motif=3).first().prix if details_extra.filter(motif=3).exists() else 0,
    }

def process_proforma_details(request, proforma):
    total_seances = 0
    cout_total = Decimal(0)
    
    for key, value in request.POST.items():
        if key.startswith('details[') and key.endswith('][quantite]'):
            detail_id = key.split('[')[1].split(']')[0]
            detail = get_object_or_404(ProformaDetails, id=detail_id)
            
            quantite = int(value)
            duree_seance = Decimal(request.POST.get(f'details[{detail_id}][duree_seance]', 0))

            nbr_seance = math.ceil(detail.idmodule.duree / duree_seance) if duree_seance > 0 else 0
            total_seances += nbr_seance
            
            detail.quantite = quantite
            detail.duree_seance = duree_seance
            detail.nbr_seance = nbr_seance
            detail.save()
            
            cout_total += detail.idmodule.prix * quantite
    
    return total_seances, cout_total

def process_new_modules(request, proforma):
    total_seances = 0
    cout_total = Decimal(0)
    
    modules = request.POST.getlist('module')
    quantites = request.POST.getlist('quantite')
    durees = request.POST.getlist('duree_seance')
    
    for i in range(len(modules)):
        module = get_object_or_404(Module, id=int(modules[i]))
        quantite = int(quantites[i])
        duree_seance = convert_time_to_hours(durees[i]) if durees[i] else None
        
        nbr_seance = math.ceil(module.duree / duree_seance) if duree_seance > 0 else 0
        total_seances += nbr_seance
        cout_total += module.prix * quantite
        
        proforma_details_data = {
            "idmodule":module,
            "quantite":quantite,
            "duree_seance":duree_seance,
            "nbr_seance":nbr_seance,
            "prix_unitaire":module.prix
        }
        if isinstance(proforma, ProformaInscrit):
            proforma_details_data['proforma_inscrit'] = proforma
        else:
            proforma_details_data['proforma_non_inscrit'] = proforma

        ProformaDetails.objects.create(
            **proforma_details_data
        )
    
    return total_seances, cout_total

def modification_proforma(request, id, proforma_model, template_name):
    if not (request.user.is_authenticated and request.user.role_utilisateur in [1, 2]):
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
    
    proforma = get_object_or_404(proforma_model, id=id)
    if request.method == "POST":
        extra = int(request.POST.get('extra', 0))
        extra_details = get_extra_details(extra)
        
        total_seances, cout_total = process_proforma_details(request, proforma)
        new_seances, new_cout = process_new_modules(request, proforma)
        total_seances += new_seances
        cout_total += new_cout
        
        nbr_frais_transport = total_seances if extra in [1, 2, 3] else 0
        nbr_location_pc = request.POST.get('nbr_location_pc', proforma.nbr_location_pc)
        if extra == 1:
            lieu_formation = Extra.objects.filter(details=extra).first().get_details_display()
            nbr_frais_restauration = hebergement = pu_hebergement = 0
        elif extra == 4:
            lieu_formation = request.POST.get('lieu_formation', '')
            hebergement = int(request.POST.get('hebergement', 0))
            pu_hebergement = Decimal(request.POST.get('pu_hebergement', 0))
            nbr_frais_restauration = int(request.POST.get('nbr_frais_restauration', 0))
        else:
            lieu_formation = request.POST.get('lieu_formation', '')
            nbr_frais_restauration = int(request.POST.get('nbr_frais_restauration', 0))
            hebergement = pu_hebergement = 0
        
        proforma.nbr_frais_transport = nbr_frais_transport
        proforma.pu_pc = extra_details['pc_pu']
        proforma.pu_transport = extra_details['transport_pu']
        proforma.pu_restauration = extra_details['restauration_pu']
        proforma.lieu_formation = lieu_formation
        proforma.nbr_frais_restauration = nbr_frais_restauration
        proforma.hebergement = hebergement
        proforma.pu_hebergement = pu_hebergement
        proforma.nbr_location_pc = nbr_location_pc
        
        cout_total += (Decimal(proforma.nbr_location_pc) * extra_details['pc_pu'] +
                       Decimal(nbr_frais_transport) * extra_details['transport_pu'] +
                       Decimal(nbr_frais_restauration) * extra_details['restauration_pu'] +
                       Decimal(hebergement) * pu_hebergement)
        
        proforma.cout_total = cout_total
        proforma.save()
        
        messages.success(request, "La modification du proforma a été effectuée avec succès.")
        # return redirect('list_proforma')
    
    context = {
        'proforma': proforma,
        'proforma_details': proforma.details.all(),
        'modules': Module.objects.all().order_by('idformation'),
        "detail_choices": Extra.DETAIL_CHOICES,
        'selected_extra': proforma.get_extra_from_location(),
    }
    return render(request, template_name, context)

@login_required
def modification_proforma_inscrit(request, id):
    return modification_proforma(request, id, ProformaInscrit, 'admin/facturation/proforma/voirProformaInscrit.html')

@login_required
def modification_proforma_non_inscrit(request, id):
    return modification_proforma(request, id, ProformaNonInscrit, 'admin/facturation/proforma/voirProformaNonInscrit.html')


# Fonction pour récupérer les prix des extras
def get_extra_prices(extra):
    details_extra = Extra.objects.filter(details=extra)
    return {
        'pc_pu': details_extra.filter(motif=2).first().prix if details_extra.filter(motif=2).first() else 0,
        'transport_pu': details_extra.filter(motif=1).first().prix if details_extra.filter(motif=1).first() else 0,
        'restauration_pu': details_extra.filter(motif=3).first().prix if details_extra.filter(motif=3).first() else 0,
        'lieu': details_extra.first().get_details_display() if details_extra.exists() else ""
    }

def process_modules(request):
    modules = request.POST.getlist('module')
    quantites = request.POST.getlist('quantite')
    durees = request.POST.getlist('duree_seance')

    total_seances = 0
    module_details = []

    for i, module_id in enumerate(modules):
        module = get_object_or_404(Module, id=int(module_id))
        quantite = int(quantites[i])
        duree_seance = convert_time_to_hours(durees[i]) if durees[i] else None
        
        nbr_seance = math.ceil(module.duree / Decimal(str(duree_seance))) if duree_seance else 0
        total_seances += nbr_seance

        module_details.append({
            'module': module,
            'quantite': quantite,
            'duree_seance': duree_seance,
            'nbr_seance': nbr_seance,
            'prix_unitaire': module.prix,
            'cout_detail': module.prix * quantite
        })
    
    return total_seances, module_details

def calculate_total_cost(module_details, nbr_location_pc, nbr_frais_transport, nbr_frais_restauration, hebergement, extra_prices):
    cout_total = Decimal(0)
    cout_total += Decimal(nbr_location_pc) * Decimal(extra_prices['pc_pu'])
    cout_total += Decimal(nbr_frais_transport) * Decimal(extra_prices['transport_pu'])
    cout_total += Decimal(nbr_frais_restauration) * Decimal(extra_prices['restauration_pu'])
    cout_total += Decimal(hebergement) * Decimal(extra_prices.get('pu_hebergement', 0))
    for detail in module_details:
        cout_total += Decimal(detail['cout_detail'])
    return cout_total

def create_proforma(model, **kwargs):
    proforma = model(**kwargs)
    proforma.full_clean()
    proforma.save()
    return proforma

# Views

@login_required
def insert_proforma_inscrit(request, id):
    if request.user.role_utilisateur not in [1, 2]:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

    client = get_object_or_404(CustomUser, id=int(id))
    if request.method == 'POST':
        extra = int(request.POST.get('extra'))
        extra_prices = get_extra_prices(extra)
        total_seances, module_details = process_modules(request)
        
        nbr_location_pc = float(request.POST.get('nbr_location_pc') or 0)
        nbr_frais_transport = total_seances if extra in [1, 2, 3] else 0
        nbr_frais_restauration = float(request.POST.get('nbr_frais_restauration', 0) or 0)
        hebergement = float(request.POST.get('hebergement', 0) or 0)
        pu_hebergement = Decimal(request.POST.get('pu_hebergement'))
        lieu_formation = extra_prices['lieu'] if extra == 1 else request.POST.get('lieu_formation')
        print(f"LIEU ICI ========= {lieu_formation}")
        cout_total = calculate_total_cost(module_details, nbr_location_pc, nbr_frais_transport, nbr_frais_restauration, hebergement, extra_prices)

        pf_inscrit = create_proforma(ProformaInscrit, idclient=client, lieu_formation=lieu_formation, nbr_location_pc=nbr_location_pc, pu_pc=extra_prices['pc_pu'], nbr_frais_transport=nbr_frais_transport, pu_transport=extra_prices['transport_pu'], nbr_frais_restauration=nbr_frais_restauration, pu_restauration=extra_prices['restauration_pu'], hebergement=hebergement, pu_hebergement=pu_hebergement, cout_total=cout_total, id_createur=request.user.id)

        for detail in module_details:
            ProformaDetails.objects.create(idmodule=detail['module'], proforma_inscrit=pf_inscrit, quantite=detail['quantite'], duree_seance=detail['duree_seance'], nbr_seance=detail['nbr_seance'], prix_unitaire=detail['prix_unitaire'])

        return redirect('list_proforma')
    
    return render(request, 'admin/facturation/proforma/inscrireProformaInscrit.html', {"client": client, 'modules': Module.objects.all().order_by('idformation'), "detail_choices": Extra.DETAIL_CHOICES})

@login_required
def insert_proforma_non_inscrit(request):
    if request.user.role_utilisateur not in [1, 2]:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")

    if request.method == 'POST':
        extra = int(request.POST.get('extra'))
        extra_prices = get_extra_prices(extra)
        total_seances, module_details = process_modules(request)
        
        nbr_location_pc = float(request.POST.get('nbr_location_pc') or 0)
        nbr_frais_transport = total_seances if extra in [1, 2, 3] else 0
        nbr_frais_restauration = float(request.POST.get('nbr_frais_restauration', 0) or 0)
        hebergement = float(request.POST.get('hebergement', 0) or 0)
        pu_hebergement = Decimal(request.POST.get('pu_hebergement'))
        lieu_formation = extra_prices['lieu'] if extra == 1 else request.POST.get('lieu_formation')
        cout_total = calculate_total_cost(module_details, nbr_location_pc, nbr_frais_transport, nbr_frais_restauration, hebergement, extra_prices)

        pf_non_inscrit = create_proforma(ProformaNonInscrit, nom=request.POST.get('nom'), prenom=request.POST.get('prenom'), nom_entreprise=request.POST.get('nom_entreprise'), adresse_entreprise=request.POST.get('adresse_entreprise'), nif=request.POST.get('nif'), stat=request.POST.get('stat'), rcs=request.POST.get('rcs'), cnaps=request.POST.get('cnaps'), lieu_formation=lieu_formation, nbr_location_pc=nbr_location_pc, pu_pc=extra_prices['pc_pu'], nbr_frais_transport=nbr_frais_transport, pu_transport=extra_prices['transport_pu'], nbr_frais_restauration=nbr_frais_restauration, pu_restauration=extra_prices['restauration_pu'], hebergement=hebergement, pu_hebergement=pu_hebergement, cout_total=cout_total, id_createur=request.user.id)

        for detail in module_details:
            ProformaDetails.objects.create(idmodule=detail['module'], proforma_non_inscrit=pf_non_inscrit, quantite=detail['quantite'], duree_seance=detail['duree_seance'], nbr_seance=detail['nbr_seance'], prix_unitaire=detail['prix_unitaire'])

        return redirect('list_proforma')
    
    return render(request, 'admin/facturation/proforma/inscrireProformaNonInscrit.html', {'modules': Module.objects.all().order_by('idformation'), "detail_choices": Extra.DETAIL_CHOICES})
