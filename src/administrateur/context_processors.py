from django.contrib.auth.models import AnonymousUser

def admin_links(request):
    """Ajoute les liens dynamiques pour les administrateurs au contexte global"""
    user = request.user

    # Définition des liens dynamiquement
    links = {}
    if user and not isinstance(user, AnonymousUser):  # Vérifie que l'utilisateur est connecté
        if user.is_staff:
            if user.role_utilisateur == 1:
                links = {
                    "Index" : "index",
                    "Liste Formateurs": "list_formateurs",
                    "Liste admin" : "list_admin",
                    "Liste client" : "list_client",
                    "Liste formation" : "list_formation",
                    "Liste module" : "list_module",
                    "Liste extra": "list_extra",
                    "Tableau de bord" : "statistiques_clients",
                    "Liste proforma" : "list_proforma",
                    "Liste facture" : "list_facture",
                    "Planning" : "liste_plannings_mensuels",
                }
            elif user.role_utilisateur == 2:
                links = {
                    "Index" : "index",
                    "Liste Formateurs": "list_formateurs",
                    "Liste client" : "list_client",
                    "Liste formation" : "list_formation",
                    "Liste module" : "list_module",
                    "Liste extra": "list_extra",
                    "Liste proforma" : "list_proforma",
                    "Liste facture" : "list_facture",
                    "Planning" : "liste_plannings_mensuels",
                }

    return {'admin_links': links}