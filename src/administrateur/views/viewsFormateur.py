from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404
from django.core.exceptions import ValidationError
from datetime import datetime
from administrateur.models import CustomUser, DetailAdmin, Formateur_competence, Module
from administrateur.utils import list_admin, inscription_admin, modifier_admin

@login_required
def list_formateurs(request):
    role_utilisateur = {
        "role" : 3
    }
    search = search_query = request.GET.get("search", "")
    role = 3
    return list_admin(request, permission=[1, 2], role_utilisateur=role_utilisateur, path='formateur/listeFormateur.html', search_query=search, role=role)
    
@login_required
def inscription_formateurs(request):
    paths = {
        "redirectionPost": "list_formateurs",
        "redirectionGet": "formateur/inscrireFormateur.html"
    }
    return inscription_admin(request=request, permission=[1, 2], path=paths, default_password='formateurAdmin', role_utilisateur=3)

@login_required
def modifier_formateur(request, id):
    paths = {
        "redirectionPost": "list_formateurs",
        "redirectionGet": "formateur/informationFormateur.html"
    }
    return modifier_admin(request=request, id=id, permission=[1, 2], path=paths)

@login_required
def competence_formateur(request, id):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        if request.method == "POST":
            formateur_id = get_object_or_404(CustomUser, id=int(id))
            formation_ids = []
            for key in request.POST:
                if key.startswith("competence_"):
                    formation_ids.append(request.POST.get(key))
            for formation_id in formation_ids:
                try:
                    formation = get_object_or_404(Module, id=int(formation_id))  # Get the module/formation
                    formateur_competence = Formateur_competence(
                        idformateur=formateur_id,
                        idmodule=formation
                    )
                    # Validate and save the new formateur competence
                    formateur_competence.full_clean()
                    formateur_competence.save()
                except ValidationError as e:
                    # Return the form with errors if validation fails
                    return render(request, 'admin/formateur/competenceFormateur.html', {
                        "formation": Module.objects.all(),
                        "errors": e.message_dict,  # Send validation errors to template
                    })

            # Redirect with a success message as a query parameter
            return redirect(f"{request.path}?success=OK")

        # Get the current formateur competencies
        competence_formateur = Formateur_competence.objects.filter(idformateur=id)
        
        # Get all available modules (formations)
        formation = Module.objects.all()

        # Check for the success query parameter
        success_message = request.GET.get('success', None)

        return render(request, "admin/formateur/competenceFormateur.html", {
            "competence_formateur": competence_formateur,
            "formation": formation,
            "success_message": success_message  # Pass the success message to the template
        })
    else:
        return HttpResponseForbidden("Vous n'avez pas l'autorisation d'accéder à cette page.")
