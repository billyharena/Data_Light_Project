from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404
from administrateur.models import Extra, StockPC
from django.core.exceptions import ValidationError


@login_required
def list_extra(request):
    if request.user.is_authenticated and request.user.role_utilisateur in [1, 2]:
        if request.method == 'POST':
            if 'extra_id' in request.POST:  # Gestion des extras
                extra_id = request.POST.get('extra_id')
                
                if extra_id:  # Modification
                    extra = get_object_or_404(Extra, id=extra_id)
                    extra.motif = request.POST.get('motif')
                    extra.details = request.POST.get('details') or None
                    extra.prix = request.POST.get('prix')
                    extra.save()
                else:  # Création
                    motif = request.POST.get('motif')
                    details = request.POST.get('details')
                    prix = request.POST.get('prix')
                    
                    if motif and prix:
                        Extra.objects.create(
                            motif=motif,
                            details=details,
                            prix=prix
                        )
            
            elif 'stock' in request.POST:  # Gestion du stock
                stock_value = request.POST.get('stock')
                stock_pc, created = StockPC.objects.get_or_create(id=1)  # On suppose qu'il n'y a qu'une seule ligne
                stock_pc.stock = stock_value
                stock_pc.save()

            return redirect('list_extra')

        extra = Extra.objects.all()
        stock_pc = StockPC.objects.first()  # Récupération du stock actuel

        return render(request, "admin/facturation/extra/extra.html", {
            "extra": extra,
            "stock_pc": stock_pc,
            "motif_choices": Extra.MOTIF_CHOICES,
            "detail_choices": Extra.DETAIL_CHOICES,
        })
    else:
        return HttpResponseForbidden("Accès non autorisé")
