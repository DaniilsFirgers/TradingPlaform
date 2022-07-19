from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, logout as dj_logout, login as dj_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm
# Create your views here.


def register(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been created! You are now being able to login")
            return redirect("/")
    else:
        form = NewUserForm()
    return render(request, "Users/register.html", {"register_form": form, "title": "Register"})


def login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                dj_login(request, user)
                messages.success(request, f"Login successful. Welcome, {username}!")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password!")
        else:
            messages.error(request, "Invalid username or password!")
    form = AuthenticationForm()
    return render(request=request, template_name="Users/login.html", context={"login_form": form, "title": "Login"})


@login_required
def logout(request):
    dj_logout(request)
    messages.info(request, "You have successfully logged out!")
    return redirect("home", {"title": "Logout"})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            messages.success(request, f"Your account has been updated!")
            return redirect('user-positions')
    else:
        u_form = UserUpdateForm(instance=request.user)

    context = {
        'u_form': u_form,
        "title": "Profile",
    }

    return render(request, 'Users/profile.html', context)