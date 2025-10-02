# In blog/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django import forms
# Note: Ensure you import UserCreationForm correctly, assuming it's imported
from django.contrib.auth.forms import UserCreationForm 
from . models import Profile, Post
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User # Redundant if from django.contrib.auth is used, but kept for context

class CustomUSerCReationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        # Removed "password1", "password2" as they are handled automatically by UserCreationForm
        fields = ("username", "email") 


# A view to handle registration of new users to the site 
def Register(request):
    if request.method == "POST":
        form = CustomUSerCReationForm(request.POST)
        if form.is_valid():
            user = form.save() 
            login(request, user)
            Profile.objects.create(user=user)
            
            return redirect("login")
    else:
        form = CustomUSerCReationForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def profile(request):
    #
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': user_profile,
        'user': request.user 
    }

    return render(request, "profile/profile.html", context) 

def home(request):
    """
    Fetches all Post objects and passes them to the template.
    """
    posts = Post.objects.all().order_by('-published_date') # Retrieves all posts, newest first
    context = {
        'posts': posts
    }
    return render(request, 'blog/home.html', context)