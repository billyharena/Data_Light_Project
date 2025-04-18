from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import FormationList, ModuleList, LogoutAPIView, ClientRegisterAPIView, ClientProfileAPIView, LoginAPIView, CreateProformaNonInscritAPIView, CreateProformaInscritAPIView, ListeProformasInscritAPIView, ProformaDetailsView, ProformaDetailsDeleteView, ProformaViewSet
from .views import FormationDetail, ClientProfileUpdateAPIView, ConvertProformaToFacture, ListeFactureInscritAPIView, FactureDetailsView, DisponibiliteFormateurAPIView, ReservationFormationAPIView, PlanningModuleAPIView
from .views import SuggestionCreneauxFormateurAPIView, EnregistrerSuggestionsAPIView

urlpatterns = [
    path('formations/', FormationList.as_view(), name='formation-list'),
    path('formations/<int:formation_id>/', FormationDetail.as_view(), name='formation-detail'),
    path('formations/<int:formation_id>/modules/', ModuleList.as_view(), name='modules-par-formation'),

    path('client/register/', ClientRegisterAPIView.as_view(), name='client_register'),
    path('client/login/', LoginAPIView.as_view(), name='client_login'),
    path('client/logout/', LogoutAPIView.as_view(), name='client_logout'),
    path('client/profile/', ClientProfileAPIView.as_view(), name='client-profile'),
    path('client/update/', ClientProfileUpdateAPIView.as_view(), name='client-profile-update'),

    path('api/client/create-proforma-non-inscrit/', CreateProformaNonInscritAPIView.as_view(), name='proforma_non_inscrit'),
    path('api/client/create-proforma-inscrit/', CreateProformaInscritAPIView.as_view(), name='proforma_inscrit'),
    path("api/proformas/", ListeProformasInscritAPIView.as_view(), name="liste_proformas"),
    path('api/proformas/<int:proforma_id>/', ProformaDetailsView.as_view(), name='proforma_details'),
    path('api/proformas/<int:proforma_id>/details/<int:detail_id>/delete/', ProformaDetailsDeleteView.as_view(), name='proforma-detail-delete'),
    path('api/proformas/<int:pk>/delete/', ProformaViewSet.as_view({'delete': 'destroy'}), name='delete_proforma'),
    path('api/proformas/<int:proforma_id>/convert-to-facture/', ConvertProformaToFacture.as_view(), name='convert_proforma_to_facture'),

    path("api/factures/", ListeFactureInscritAPIView.as_view(), name="liste_factures"),
    path('api/factures/<int:facture_id>/', FactureDetailsView.as_view(), name='facture_details'),

    path('api/planning/<int:module_id>/<str:mois>/', DisponibiliteFormateurAPIView.as_view(), name='disponibilite-formateur'),
    path('api/reservations/', ReservationFormationAPIView.as_view(), name='reservations'),
    path('api/planning_module/<int:module_id>/<int:detailfacture_id>/<int:facture_id>/', PlanningModuleAPIView.as_view(), name='planning_module'),

    path('api/modules/<int:module_id>/disponibilites/<str:mois>/suggestions/',
        SuggestionCreneauxFormateurAPIView.as_view(),
        name='suggestion_creneaux_formateur'),
    path('api/reservations-suggestions/', EnregistrerSuggestionsAPIView.as_view(), name='enregistrer_suggestions'),
    # path('api/client/facture-non-inscrit/', FactureNonInscritAPIView.as_view(), name='facture_non_inscrit'),
    # path('api/client/facture-inscrit/', FactureInscritAPIView.as_view(), name='facture_inscrit'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)