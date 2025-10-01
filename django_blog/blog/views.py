from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django import forms
from . models import User, Profile, Post
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

class CustomUSerCReationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

#a view to handle registration of new users to the site 


def Register(request):
    if request.method == "POST":
        form = CustomUSerCReationForm(request.POST)
        if form.is_valid():
            # Save the new user object
            user = form.save() 
            
            # --- FIX: Create the corresponding Profile object ---
            Profile.objects.create(user=user)
            
            return redirect("login")
    else:
        form = CustomUSerCReationForm()
    return render(request, "registration/register.html", {"form": form})
@login_required
def profile(request):
    return render(request, "registration/profile.html")



def home(request):
    """
    Fetches all Post objects and passes them to the template.
    """
    posts = Post.objects.all().order_by('-published_date') # Retrieves all posts, newest first
    context = {
        'posts': posts
    }
    return render(request, "django_blog\blog\template\blog\home.html", context)