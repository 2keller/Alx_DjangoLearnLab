from urllib import request
from django.shortcuts import render
import random 
from .models import LogEntry
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages 

# Create your views here.
star_trek_quotes = [
    "Live long and prosper.",
    "To boldly go where no one has gone before.",
    "The needs of the many outweigh the needs of the few, or the one.",
    "Space: the final frontier.",
    "Logic is the beginning of wisdom, not the end.",
    "It is possible to commit no mistakes and still lose. That is not a weakness; that is life.",
    "Change is the essential process of all existence.",
    "Things are only impossible until they're not.",
    "I don't believe in a no-win scenario.",
    "We work to better ourselves and the rest of humanity.",
    "Sometimes a feeling is all we humans have to go on.",
    "Time is a companion who goes with us on the journey and reminds us to cherish every moment.",
    "Without freedom of choice, there is no creativity.",
    "The prejudices people feel about each other disappear when they get to know each other.",
    "With the first link, the chain is forged.",
    "A library serves no purpose unless someone is using it.",
    "Improve a mechanical device and you may double productivity. But improve man, you gain a thousandfold.",
    "Compassion: that’s the one thing no machine ever had. Maybe it’s the one thing that keeps men ahead of them.",
    "You can use logic to justify almost anything. That’s its power. And its flaw.",
    "There is a way out of every box, a solution to every puzzle; it’s just a matter of finding it.",
    "What we leave behind is not as important as how we’ve lived.",
    "A man either lives life as it happens to him, meets it head-on and licks it, or he turns his back on it and starts to wither away.",
    "Having is not so pleasing a thing as wanting. This is not logical, but it is often true.",
    "I have been, and always shall be, your friend.",
    "It is the unknown that defines our existence.",
    "There are always possibilities.",
    "Evil does seek to maintain power by suppressing the truth.",
    "Without followers, evil cannot spread.",
    "Humans do have an amazing capacity for believing what they choose — and excluding that which is painful.",
    "If we’re going to be damned, let’s be damned for what we really are.",
    "Your will to survive, your love of life, your passion to know … those are the qualities that make a civilization worthy to survive.",
    "The whole show was an attempt to say that humanity will reach maturity and wisdom on the day that it begins not just to tolerate, but to take a special delight in differences.",
    "We are explorers; we explore our lives, day by day, and we explore the galaxy, trying to expand the boundaries of our knowledge.",
    "Someone once told me that time was a predator that stalked us all our lives. I rather believe that time is a companion.",
    "What makes one man an exceptional leader? We see indications that it’s his negative side which makes him strong.",
    "Computers make excellent and efficient servants, but I have no wish to serve under them.",
    "A species that enslaves itself to its own technology is not truly civilized.",
    "Let me help. Let me help because I care.",
    "Fear exists for one purpose: to be conquered.",
    "The first duty of every Starfleet officer is to the truth.",
    "In critical moments, men sometimes see exactly what they wish to see.",
    "Live now; make now always the most precious time. Now will never come again.",
    "A starship is no place for a man to grow old.",
    "Insufficient facts always invite danger.",
    "The mind’s ability to reason must be harnessed to solve any conflict or problem.",
    "The future is the undiscovered country.",
    "The power of command begins to elude you when your negative side is removed.",
    "Let us redefine progress to mean that just because we can do a thing, it does not necessarily mean we must do that thing.",
    "Human beings do not survive on bread alone … but on the nourishments of liberty.",
    "We tried to say that the worst possible thing that can happen to all of us is for the future to press us into a common mold.",
]

def home(request):
    recent_logs = None
    if request.user.is_authenticated:
        recent_logs = LogEntry.objects.filter(user=request.user).order_by('-timestamp')[:3]
    
    context = {
        'recent_logs': recent_logs
    }
    return render(request, 'logs/home.html', context)

@login_required
def view_logs(request):
    logs = LogEntry.objects.filter(user=request.user).order_by('-timestamp')
    
    # Initialize variables
    search_query = None
    level_filter = None

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        logs = logs.filter(content__icontains=search_query)
    
    # Filter by level
    level_filter = request.GET.get('level')
    if level_filter:
        logs = logs.filter(level=level_filter)
    
    # Pagination
    paginator = Paginator(logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'search_query': search_query,
        'level_filter': level_filter,
        'levels': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    }
    return render(request, 'logs/view_logs.html', context)

@login_required
def create_log(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        level = request.POST.get('level', 'INFO')
        quote = random.choice(star_trek_quotes)
        LogEntry.objects.create(user=request.user, content=content, level=level, star_trek_quote=quote)
        return redirect('view_logs')
    return render(request, 'logs/create_logs.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'logs/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'logs/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')
