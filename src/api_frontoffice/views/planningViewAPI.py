import random
from datetime import datetime, time, timedelta, date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from collections import defaultdict
from django.db.models import Q
from decimal import Decimal
from administrateur.models import Formateur_competence, PlanningFormation, CustomUser, Module, FactureDetails, FactureInscrit

"""
    Rechercher les dates indisponible de chaque formateurs
    Si dans une date, il y a x formateurs indisponibles et y formateur disponibles
    Marquer la date comme disponible
"""

class DisponibiliteFormateurAPIView(APIView):
    """
    API pour obtenir les créneaux où tous les formateurs sont indisponibles en même temps.
    """

    def get(self, request, module_id, mois):
        try:
            try:
                annee, mois = map(int, mois.split("-"))
            except ValueError:
                return Response({"error": "Format du mois invalide, attendu: YYYY-MM"}, status=status.HTTP_400_BAD_REQUEST)

            module = get_object_or_404(Module, id=module_id)
            duree_module = module.duree
            module_name = f"{module.module} (Formation: {module.idformation.formation})"

            formateurs_ids = Formateur_competence.objects.filter(idmodule=module_id).values_list('idformateur', flat=True)
            if not formateurs_ids:
                return Response({"message": "Aucun formateur trouvé pour ce module.", "duree_module": duree_module}, status=status.HTTP_404_NOT_FOUND)

            formateurs = CustomUser.objects.filter(id__in=formateurs_ids)
            total_formateurs = len(formateurs)

            calendrier = defaultdict(lambda: {"morning": set(), "afternoon": set()})

            for formateur in formateurs:
                formations = PlanningFormation.objects.filter(
                    idformateur=formateur,
                    dateFormation__year=annee,
                    dateFormation__month=mois
                ).values("dateFormation", "heureDebFormation", "heureFinFormation")

                for formation in formations:
                    date = formation["dateFormation"]
                    start_time = formation["heureDebFormation"]
                    end_time = formation["heureFinFormation"]

                    if self.time_overlap(start_time, end_time, time(8, 0), time(12, 0)):
                        calendrier[date]["morning"].add(formateur.id)

                    if self.time_overlap(start_time, end_time, time(13, 0), time(17, 0)):
                        calendrier[date]["afternoon"].add(formateur.id)

            indisponibilites_communes = defaultdict(list)
            for date, periodes in calendrier.items():
                for periode, formateurs_indispo in periodes.items():
                    if len(formateurs_indispo) == total_formateurs:
                        indisponibilites_communes[periode].append({
                            "dateFormation": date,
                            "heureDebFormation": "08:00:00" if periode == "morning" else "13:00:00",
                            "heureFinFormation": "12:00:00" if periode == "morning" else "17:00:00",
                        })

            result = []
            for formateur in formateurs:
                indispos = []
                for periode, formations in indisponibilites_communes.items():
                    indispos.extend(formations)

                result.append({
                    "idformateur": formateur.id,
                    "duree_module": duree_module,
                    "module": module_name,
                    "indisponibilites": indispos
                })

            # Si aucun formateur n'a d'indisponibilité, on retourne quand même la durée du module
            if not result:
                return Response({"duree_module": duree_module, "indisponibilites": []}, status=status.HTTP_200_OK)

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def time_overlap(self, start1, end1, start2, end2):
        """Vérifie si deux plages horaires se chevauchent."""
        return max(start1, start2) < min(end1, end2)


    """
        API pour réserver une formation pour un client.

        1 - Recevoir les informations venant du front-office
            - ID du module
            - ID du module dans detail_facture
            - les slots choisis par le client
        2 - Vérifier que le detail_facture appartient réelement au client
        3 - Vérifier que la durée total des slots est égale à la durée du module
        4 - Choisir un formateur qui est libre parmi les slots choisit par le client
    """
class ReservationFormationAPIView(APIView):
    """
    API pour réserver une formation pour un client avec un formateur unique.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        module_id = request.data.get('moduleId')
        detailfacture_id = request.data.get('detailId')
        facture_id = request.data.get('factureId')
        slots = request.data.get('slots', [])

        if not all([module_id, detailfacture_id, facture_id, slots]):
            return Response({"Erreur": "Données incomplètes."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérification que la facture appartient bien au client connecté
        detail_facture = get_object_or_404(FactureDetails, id=detailfacture_id)
        facture = get_object_or_404(FactureInscrit, id=facture_id)

        if facture.idclient != request.user:
            return Response({"Erreur": "Vous ne pouvez pas réserver une formation qui ne vous appartient pas."}, status=status.HTTP_403_FORBIDDEN)

        # Vérification de la durée totale des créneaux choisis
        module = get_object_or_404(Module, id=module_id)

        def calculer_duree(heure_debut, heure_fin):
            """ Calcule la durée en heures entre deux horaires """
            fmt = "%H:%M"
            debut = datetime.strptime(heure_debut, fmt)
            fin = datetime.strptime(heure_fin, fmt)
            return (fin - debut).seconds / 3600  # Convertir en heures

        # Ajouter la durée calculée à chaque slot
        for slot in slots:
            slot["duree"] = calculer_duree(slot["heureDebut"], slot["heureFin"])

        total_duree = sum(slot['duree'] for slot in slots)

        if total_duree != float(module.duree):
            return Response({"Erreur": f"La somme des créneaux ne correspond pas à la durée du module({int(module.duree)}h)."}, status=status.HTTP_400_BAD_REQUEST)

        # Étape 1 : Trouver les formateurs compétents pour ce module
        formateurs_competents_ids = Formateur_competence.objects.filter(
            idmodule=module_id
        ).values_list('idformateur', flat=True)

        # Étape 2 : Trouver les formateurs disponibles pour chaque créneau
        formateurs_disponibles_par_slot = []
        
        for slot in slots:
            date = slot["date"]
            heure_debut = slot["heureDebut"]
            heure_fin = slot["heureFin"]

            # Trouver les formateurs disponibles pour ce créneau précis
            formateurs_disponibles = CustomUser.objects.filter(
                id__in=formateurs_competents_ids
            ).exclude(
                planning_formateur__dateFormation=date,
                planning_formateur__heureDebFormation__lt=heure_fin,
                planning_formateur__heureFinFormation__gt=heure_debut,
                planning_formateur__heureDebFormation__lte=heure_fin,  # Évite les chevauchements exacts
                planning_formateur__heureFinFormation__gte=heure_debut  # Évite les chevauchements exacts
            ).values_list('id', flat=True)


            formateurs_disponibles_par_slot.append(set(formateurs_disponibles))

        # Étape 3 : Trouver l'intersection (formateurs disponibles pour **tous** les créneaux)
        formateurs_potentiels = set.intersection(*formateurs_disponibles_par_slot) if formateurs_disponibles_par_slot else set()

        if not formateurs_potentiels:
            return Response({"Erreur": "Aucun formateur n'est disponible pour tous les créneaux."}, status=status.HTTP_400_BAD_REQUEST)

        # Étape 4 : Identifier les formateurs ayant déjà travaillé avec ce client
        formateurs_deja_affectes = PlanningFormation.objects.filter(
            idformateur__in=formateurs_potentiels,
            idfacturedetail__facture_inscrit__idclient=request.user  # Chemin corrigé
        ).values_list('idformateur', flat=True)

        # Sélectionner un formateur privilégié
        formateur_choisi = None
        for formateur_id in formateurs_deja_affectes:
            if formateur_id in formateurs_potentiels:
                formateur_choisi = formateur_id
                break

        # Si aucun formateur privilégié, choisir au hasard
        if not formateur_choisi:
            formateur_choisi = random.choice(list(formateurs_potentiels))

        # Étape 5 : Réserver les créneaux pour ce formateur unique
        for slot in slots:
            PlanningFormation.objects.create(
                idformateur_id=formateur_choisi,
                idmodule=module,
                idfacturedetail=detail_facture,  # AJOUTEZ CE CHAMP OBLIGATOIRE
                dateFormation=slot["date"],
                heureDebFormation=slot["heureDebut"],
                heureFinFormation=slot["heureFin"]
            )

        return Response({
            "message": "Réservation effectuée avec succès.",
            "formateur_id": formateur_choisi
        }, status=status.HTTP_201_CREATED)
        
class PlanningModuleAPIView(APIView):
    """
    API pour obtenir le planning d'un module
    """
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, module_id, detailfacture_id, facture_id):
        # Vérification de l'existence du module
        module = get_object_or_404(Module, id=module_id)

        # Vérification de l'existence du détail de la facture
        facture_detail = get_object_or_404(FactureDetails, id=detailfacture_id)
        facture = get_object_or_404(FactureInscrit, id=facture_id)

        if facture.idclient != request.user:
            return Response({"Erreur": "Vous ne pouvez pas réserver une formation qui ne vous appartient pas."}, status=status.HTTP_403_FORBIDDEN)

        # Vérification que le module appartient bien au détail de la facture
        if facture_detail.idmodule != module:
            return Response({"Erreur": "Le module spécifié ne correspond pas au détail de la facture."}, status=status.HTTP_400_BAD_REQUEST)

        # Récupération du planning du module
        planning = PlanningFormation.objects.filter(
            idmodule=module,
            idfacturedetail=facture_detail
        ).values('dateFormation', 'heureDebFormation', 'heureFinFormation')

        # Ajout du nom du module et de la formation
        response_data = {
            "module": module.module,
            "formation": module.idformation.formation,
            "planning": list(planning)
        }

        return Response(response_data, status=status.HTTP_200_OK)


class SuggestionCreneauxFormateurAPIView(APIView):
    """
    API pour suggérer des créneaux de formation pour un formateur choisi aléatoirement
    parmi ceux compétents et potentiellement disponibles sur la semaine,
    afin d'atteindre la durée totale d'un module.
    """

    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, module_id, mois):
        try:
            try:
                annee, mois = map(int, mois.split("-"))
            except ValueError:
                return Response({"error": "Format du mois invalide, attendu: AAAA-MM"}, status=status.HTTP_400_BAD_REQUEST)

            module = get_object_or_404(Module, id=module_id)
            duree_module_en_heures = Decimal(str(module.duree))  # Convertir en Decimal ici
            module_name = f"{module.module} (Formation: {module.idformation.formation})"

            # Récupérer les IDs des formateurs compétents pour ce module
            formateurs_competents_ids = Formateur_competence.objects.filter(idmodule=module_id).values_list('idformateur', flat=True)
            if not formateurs_competents_ids:
                return Response({"message": "Aucun formateur compétent trouvé pour ce module.", "duree_module": float(duree_module_en_heures)}, status=status.HTTP_404_NOT_FOUND)

            formateurs_competents = CustomUser.objects.filter(id__in=formateurs_competents_ids, role_utilisateur=3)
            if not formateurs_competents:
                return Response({"message": "Aucun formateur compétent trouvé (détail).", "duree_module": float(duree_module_en_heures)}, status=status.HTTP_404_NOT_FOUND)

            formateurs_disponibles_semaine = []
            premier_jour_mois = date(annee, mois, 1)
            dernier_jour_mois = date(annee, mois + 1, 1) - timedelta(days=1)

            for formateur in formateurs_competents:
                if self.est_potentiellement_disponible_semaine(formateur, annee, mois):
                    formateurs_disponibles_semaine.append(formateur)

            if not formateurs_disponibles_semaine:
                return Response({"message": "Aucun formateur compétent et potentiellement disponible sur la semaine trouvé pour ce module.", "duree_module": float(duree_module_en_heures)}, status=status.HTTP_404_NOT_FOUND)

            # Choisir un formateur aléatoirement parmi ceux disponibles
            formateur_choisi = random.choice(formateurs_disponibles_semaine)

            # Récupérer les planifications du formateur choisi pour le mois
            plannings_formateur = PlanningFormation.objects.filter(
                idformateur=formateur_choisi,
                dateFormation__year=annee,
                dateFormation__month=mois
            ).values("dateFormation", "heureDebFormation", "heureFinFormation")

            # Créer un calendrier d'indisponibilités pour le formateur choisi
            indisponibilites_formateur = defaultdict(list)
            for planning in plannings_formateur:
                date_formation = planning["dateFormation"]
                heure_debut = planning["heureDebFormation"]
                heure_fin = planning["heureFinFormation"]
                indisponibilites_formateur[date_formation].append((heure_debut, heure_fin))

            # Générer des suggestions de créneaux disponibles pour atteindre la durée du module
            suggestions = self.generer_suggestions(formateur_choisi, duree_module_en_heures, annee, mois, indisponibilites_formateur)

            return Response({
                "formateur_id": formateur_choisi.id,
                "formateur_nom": f"{formateur_choisi.prenom} {formateur_choisi.nom}",
                "module": module_name,
                "duree_module_requise": float(duree_module_en_heures),
                "suggestions": suggestions
            }, status=status.HTTP_200_OK)

        except Module.DoesNotExist:
            return Response({"error": f"Module avec l'ID {module_id} non trouvé."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def est_potentiellement_disponible_semaine(self, formateur, annee, mois):
        """
        Vérifie si un formateur a des disponibilités potentielles sur une semaine type (Lundi-Vendredi)
        du mois donné. On vérifie s'il a au moins un créneau libre chaque jour.
        """
        premier_jour_mois = date(annee, mois, 1)
        dernier_jour_mois = date(annee, mois + 1, 1) - timedelta(days=1)
        disponibilite_par_jour = defaultdict(lambda: {"matin": True, "apres_midi": True})

        plannings_formateur = PlanningFormation.objects.filter(
            idformateur=formateur,
            dateFormation__year=annee,
            dateFormation__month=mois
        ).values("dateFormation", "heureDebFormation", "heureFinFormation")

        for planning in plannings_formateur:
            date_formation = planning["dateFormation"]
            heure_debut = planning["heureDebFormation"]
            heure_fin = planning["heureFinFormation"]

            debut_matin = time(8, 0)
            fin_matin = time(12, 0)
            debut_apres_midi = time(13, 0)
            fin_journee = time(17, 0)

            if self.time_overlap(heure_debut, heure_fin, debut_matin, fin_matin):
                disponibilite_par_jour[date_formation]["matin"] = False
            if self.time_overlap(heure_debut, heure_fin, debut_apres_midi, fin_journee):
                disponibilite_par_jour[date_formation]["apres_midi"] = False

        # Vérifier la disponibilité sur une semaine type (du lundi au vendredi) du mois
        for i in range(5):  # Lundi (0) à Vendredi (4)
            jour_cible = premier_jour_mois
            jours_verifies = 0
            while jour_cible <= dernier_jour_mois:
                if jour_cible.weekday() == i:
                    if disponibilite_par_jour[jour_cible]["matin"] or disponibilite_par_jour[jour_cible]["apres_midi"]:
                        jours_verifies += 1
                        break  # Au moins un créneau disponible ce jour
                jour_cible += timedelta(days=1)
            if jours_verifies == 0:
                return False  # Pas de disponibilité potentielle pour au moins un jour de la semaine

        return True

    def generer_suggestions(self, formateur, duree_module, annee, mois, indisponibilites):
        suggestions = []
        duree_restante = Decimal(str(duree_module))
        premier_jour_mois = date(annee, mois, 1)
        dernier_jour_mois = date(annee, mois + 1, 1) - timedelta(days=1)
        jour_actuel = premier_jour_mois  # Commencer au premier jour du mois
        aujourdhui = date.today()

        # Calculer le premier jour de la semaine suivante (ou aujourd'hui si c'est lundi)
        jours_jusqua_lundi = (7 - aujourdhui.weekday()) % 7
        debut_suggestions = aujourdhui + timedelta(days=jours_jusqua_lundi)

        # Si le mois demandé est le mois en cours, commencer les suggestions à partir du début de la semaine suivante
        if annee == aujourdhui.year and mois == aujourdhui.month:
            jour_actuel = max(debut_suggestions, jour_actuel)

        while duree_restante > Decimal('0') and jour_actuel <= dernier_jour_mois:
            # Vérifier si le jour actuel n'est pas un dimanche (weekday() == 6 pour dimanche)
            if jour_actuel.weekday() != 6:
                debut_journee = time(8, 0)
                fin_matin = time(12, 0)
                debut_apres_midi = time(13, 0)
                fin_journee = time(17, 0)

                # Vérifier la disponibilité le matin
                if duree_restante > Decimal('0'):
                    disponible_matin = True
                    for indispo in indisponibilites.get(jour_actuel, []):
                        if self.time_overlap(debut_journee, fin_matin, indispo[0], indispo[1]):
                            disponible_matin = False
                            break
                    if disponible_matin:
                        duree_possible_float = (datetime.combine(jour_actuel, fin_matin) - datetime.combine(jour_actuel, debut_journee)).total_seconds() / 3600
                        duree_possible = Decimal(str(duree_possible_float))

                        if duree_restante >= duree_possible and duree_possible > Decimal('0'):
                            suggestions.append({
                                "dateFormation": jour_actuel,
                                "heureDebFormation": debut_journee.strftime("%H:%M:%S"),
                                "heureFinFormation": fin_matin.strftime("%H:%M:%S"),
                                "duree_en_heures": float(duree_possible)
                            })
                            duree_restante -= duree_possible
                        elif duree_restante > Decimal('0') and duree_possible > Decimal('0'):
                            duree_a_planifier = min(duree_restante, duree_possible)
                            heure_fin_suggestion_dt = datetime.combine(jour_actuel, debut_journee) + timedelta(hours=float(duree_a_planifier))
                            heure_fin_suggestion = heure_fin_suggestion_dt.time()
                            suggestions.append({
                                "dateFormation": jour_actuel,
                                "heureDebFormation": debut_journee.strftime("%H:%M:%S"),
                                "heureFinFormation": heure_fin_suggestion.strftime("%H:%M:%S"),
                                "duree_en_heures": float(duree_a_planifier)
                            })
                            duree_restante -= duree_a_planifier

                # Vérifier la disponibilité l'après-midi
                if duree_restante > Decimal('0'):
                    disponible_apres_midi = True
                    for indispo in indisponibilites.get(jour_actuel, []):
                        if self.time_overlap(debut_apres_midi, fin_journee, indispo[0], indispo[1]):
                            disponible_apres_midi = False
                            break
                    if disponible_apres_midi:
                        duree_possible_float = (datetime.combine(jour_actuel, fin_journee) - datetime.combine(jour_actuel, debut_apres_midi)).total_seconds() / 3600
                        duree_possible = Decimal(str(duree_possible_float))

                        if duree_restante >= duree_possible and duree_possible > Decimal('0'):
                            suggestions.append({
                                "dateFormation": jour_actuel,
                                "heureDebFormation": debut_apres_midi.strftime("%H:%M:%S"),
                                "heureFinFormation": fin_journee.strftime("%H:%M:%S"),
                                "duree_en_heures": float(duree_possible)
                            })
                            duree_restante -= duree_possible
                        elif duree_restante > Decimal('0') and duree_possible > Decimal('0'):
                            duree_a_planifier = min(duree_restante, duree_possible)
                            heure_fin_suggestion_dt = datetime.combine(jour_actuel, debut_apres_midi) + timedelta(hours=float(duree_a_planifier))
                            heure_fin_suggestion = heure_fin_suggestion_dt.time()
                            suggestions.append({
                                "dateFormation": jour_actuel,
                                "heureDebFormation": debut_apres_midi.strftime("%H:%M:%S"),
                                "heureFinFormation": heure_fin_suggestion.strftime("%H:%M:%S"),
                                "duree_en_heures": float(duree_a_planifier)
                            })
                            duree_restante -= duree_a_planifier

            jour_actuel += timedelta(days=1)
        print(f"Suggestions générées: {suggestions}")
        return suggestions

    def time_overlap(self, start1_time, end1_time, start2_time, end2_time):
        """Vérifie si deux plages horaires (time objects) se chevauchent."""
        start1 = datetime.combine(date.today(), start1_time)
        end1 = datetime.combine(date.today(), end1_time)
        start2 = datetime.combine(date.today(), start2_time)
        end2 = datetime.combine(date.today(), end2_time)
        return max(start1, start2) < min(end1, end2)


class EnregistrerSuggestionsAPIView(APIView):
    """
    API pour enregistrer les créneaux suggérés dans le planning de formation.
    Met à jour le nombre de frais de transport en fonction du nombre de jours de formation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        module_id = request.data.get('moduleId')
        detailfacture_id = request.data.get('detailId')
        facture_id = request.data.get('factureId')
        suggestions = request.data.get('suggestions', [])
        formateur_id = request.data.get('formateurId')

        if not all([module_id, detailfacture_id, facture_id, suggestions, formateur_id]):
            return Response({"Erreur": "Données incomplètes pour enregistrer les suggestions."}, status=status.HTTP_400_BAD_REQUEST)

        module = get_object_or_404(Module, id=module_id)
        detail_facture = get_object_or_404(FactureDetails, id=detailfacture_id)
        facture = get_object_or_404(FactureInscrit, id=facture_id)
        formateur = get_object_or_404(CustomUser, id=formateur_id, role_utilisateur=3)

        if facture.idclient != request.user:
            return Response({"Erreur": "Vous ne pouvez pas enregistrer de planning pour une facture qui ne vous appartient pas."}, status=status.HTTP_403_FORBIDDEN)

        total_duree_suggestion = sum(Decimal(str(suggestion.get('duree_en_heures', 0))) for suggestion in suggestions)
        if total_duree_suggestion != Decimal(str(module.duree)):
            return Response({"Avertissement": f"La somme des durées suggérées ({total_duree_suggestion}h) ne correspond pas exactement à la durée requise du module ({module.duree}h). Les créneaux seront enregistrés tels quels."}, status=status.HTTP_200_OK)

        jours_formation = set()
        planning_enregistre = []
        for suggestion in suggestions:
            date_formation_str = suggestion.get('dateFormation')
            heure_deb_formation = suggestion.get('heureDebFormation')
            heure_fin_formation = suggestion.get('heureFinFormation')

            if all([date_formation_str, heure_deb_formation, heure_fin_formation]):
                try:
                    date_formation = datetime.strptime(date_formation_str, '%Y-%m-%d').date()
                    PlanningFormation.objects.create(
                        idformateur=formateur,
                        idmodule=module,
                        idfacturedetail=detail_facture,
                        dateFormation=date_formation,
                        heureDebFormation=heure_deb_formation,
                        heureFinFormation=heure_fin_formation
                    )
                    planning_enregistre.append({
                        "dateFormation": date_formation_str,
                        "heureDebFormation": heure_deb_formation,
                        "heureFinFormation": heure_fin_formation
                    })
                    jours_formation.add(date_formation)
                except ValueError:
                    return Response({"Erreur": "Format de date invalide dans les suggestions."}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({"Erreur lors de l'enregistrement d'un créneau": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"Erreur": "Données de créneau suggéré incomplètes."}, status=status.HTTP_400_BAD_REQUEST)

        # Mettre à jour nbr_frais_transport en fonction du nombre de jours de formation
        facture.nbr_frais_transport = len(jours_formation)
        facture.save()

        detail_facture.estPlannifie = True
        detail_facture.save()

        return Response({
            "message": "Créneaux suggérés enregistrés dans le planning avec succès.",
            "nombre_jours_formation": len(jours_formation),
            "nouveau_nbr_frais_transport": facture.nbr_frais_transport,
            "planning": planning_enregistre,
            "formateur_id": formateur.id,
            "formateur_nom": f"{formateur.prenom} {formateur.nom}",
            "module": module.module
        }, status=status.HTTP_201_CREATED)