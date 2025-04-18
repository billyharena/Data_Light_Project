from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, Http404
from datetime import datetime
from administrateur.models import CustomUser, DetailAdmin

def index(request):
    if request.user.is_authenticated:
        user = request.user
        print(f"USER ==== {user}")
        detail_admin = DetailAdmin.objects.filter(utilisateur=user).first()
        print(f"++++++++++++++{detail_admin}")
        return render(request, 'admin/accueil.html', {
            'user': user,
            'detail_admin': detail_admin
        })
    else:
        return redirect('login')

# Create your views here.
def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                return redirect('index')
            else:
                logout(request)
                return render(request, 'admin/registration/login.html', {'error': "Pas d'autorisation !"})
                
    
    return render(request, 'admin/registration/login.html')

def logout_user(request):
    logout(request)
    return redirect('login')