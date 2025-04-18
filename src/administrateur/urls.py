from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views.views import index, login_user, logout_user
from .views.viewsFormateur import list_formateurs, inscription_formateurs, modifier_formateur, competence_formateur
from .views.viewsAdmin import list_admins, inscription_admins, modifier_admins, statistiques_clients
from .views.viewsClient import list_client, modifier_client, inscription_client
from .views.viewsFormation import list_formation, inscription_formation, modifier_formation, list_module, inscription_module, modifier_module
from .views.viewsProforma import list_proforma, insert_proforma_inscrit, modification_proforma_inscrit, supprimer_proforma_detail, insert_proforma_non_inscrit, modification_proforma_non_inscrit
from .views.viewsFacture import list_facture, convertir_proforma_en_facture, inscrire_facture_non_inscrit, voir_facture_non_inscrit, voir_facture_inscrit
from .views.viewsPlanning import creer_planning, liste_plannings_mensuels
from .views.viewsExtra import list_extra
from .views.viewsFmfp import remplir_formulaire, generer_rie

urlpatterns = [
    path('', index, name='index'),
    path('logout/', logout_user, name='logout'),
    path('login/', login_user, name='login'),

    path('formateurs/', list_formateurs, name='list_formateurs'),
    path('formateurs/inscription/', inscription_formateurs, name='inscription_formateurs'),
    path('formateurs/modifier/formateur-<int:id>', modifier_formateur, name='modifier_formateur'),
    path('formateur/competence-<int:id>', competence_formateur, name='formateur_competence'),

    path('admin/', list_admins, name='list_admin'),
    path('admin/inscription/', inscription_admins, name='inscription_admin'),
    path('admin/modifier/admin-<int:id>', modifier_admins, name='modifier_admin'),

    path('client/', list_client, name='list_client'),
    path('client/inscription/', inscription_client, name='inscription_client'),
    path('client/modifier/client-<int:id>', modifier_client, name='modifier_client'),

    path('formation/', list_formation, name='list_formation'),
    path('formation/inscription/', inscription_formation, name='inscription_formation'),
    path('formation/modifier/formation-<int:id>', modifier_formation, name='modifier_formation'),

    path('formation/module', list_module, name='list_module'),
    path('formation/module/ajout-module/', inscription_module, name='inscription_module'),
    path('formation/module/modifier-<int:id>', modifier_module, name='modifier_module'),

    path('dashboard/', statistiques_clients, name='statistiques_clients'),

    path('proforma/', list_proforma, name='list_proforma'),
    path('proformat/inscrit/ajout-<int:id>', insert_proforma_inscrit, name='inscription_proforma_inscrit'),
    path('proforma/convertir-facture-<int:id>', convertir_proforma_en_facture, name='convertir_proforma_en_facture'),
    path('proforma/modifier/proforma-inscrit-<int:id>', modification_proforma_inscrit, name='modification_proforma_inscrit'),
    path('proforma/detail/supprimer/<int:detail_id>/', supprimer_proforma_detail, name='supprimer_proforma_detail'),

    path('proforma/non_inscrit/ajout/', insert_proforma_non_inscrit, name='inscription_proforma_non_inscrit'),
    path('facture/non-inscrit/inscrire/<int:id>/', inscrire_facture_non_inscrit, name='inscrire_facture_non_inscrit'),
    path('proforma/non_inscrit/modification-<int:id>', modification_proforma_non_inscrit, name="modification_proforma_non_inscrit"),

    path('facture/', list_facture, name='list_facture'),
    path('facture/non_inscrit/voir-<int:id>', voir_facture_non_inscrit, name='voir_facture_non_inscrit'),
    path('facture/inscrit/voir-<int:id>', voir_facture_inscrit, name='voir_facture_inscrit'),

    path('planning/creer/<int:facture_detail_id>/', creer_planning, name='creer_planning'),
    path('planning/', liste_plannings_mensuels, name='liste_plannings_mensuels'),

    path('extra/', list_extra, name="list_extra"),

    path('formulaire/', remplir_formulaire, name='remplir_formulaire'),
    path('generer-rie/<int:proforma_id>/', generer_rie, name='generer_rie'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)