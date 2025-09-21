# feelings/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth import login, get_user_model
from django.db.models import Q
from .models import Post, Profile, Reaction, Comment
User = get_user_model()
from .forms import PostForm, SignUpForm, ProfileForm, CommentForm

def feed_view(request):
    posts = Post.objects.select_related('user', 'user__profile').all()
    comment_form = CommentForm()
    return render(request, 'feelings/feed.html', {'posts': posts, 'comment_form': comment_form})

@login_required
def create_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'Your post has been shared! 💙')
            return redirect('feelings:feed')
    else:
        form = PostForm()
    return render(request, 'feelings/create_post.html', {'form': form})

@login_required
def react_view(request, post_id, reaction):
    if request.method != 'POST':
        return HttpResponseForbidden("Use POST to react.")
    
    post = get_object_or_404(Post, id=post_id)
    
    if reaction not in ['hug', 'tear']:
        return HttpResponseForbidden("Invalid reaction.")
    
    # Check if user already reacted to this post
    existing_reaction = Reaction.objects.filter(
        user=request.user, 
        post=post, 
        reaction_type=reaction
    ).first()
    
    if existing_reaction:
        # Remove the reaction
        existing_reaction.delete()
        if reaction == 'hug':
            post.hugs = max(0, post.hugs - 1)
        else:
            post.tears = max(0, post.tears - 1)
        post.save()
        messages.info(request, f'Removed {reaction} reaction')
    else:
        # Add new reaction
        Reaction.objects.create(
            user=request.user,
            post=post,
            reaction_type=reaction
        )
        if reaction == 'hug':
            post.hugs += 1
        else:
            post.tears += 1
        post.save()
        messages.success(request, f'Added {reaction} reaction!')
    
    return redirect('feelings:feed')

@login_required
def add_comment_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method != 'POST':
        return HttpResponseForbidden('Use POST to comment.')
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
        messages.success(request, 'Comment added! 💬')
    else:
        messages.error(request, 'Please write a valid comment.')
    return redirect('feelings:feed')

@login_required
def edit_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        return HttpResponseForbidden("You can only edit your own posts.")
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully! ✨')
            return redirect('feelings:feed')
    else:
        form = PostForm(instance=post)
    
    return render(request, 'feelings/edit_post.html', {'form': form, 'post': post})

@login_required
def delete_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        return HttpResponseForbidden("You can only delete your own posts.")
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully! 🗑️')
        return redirect('feelings:feed')
    
    return render(request, 'feelings/delete_post.html', {'post': post})

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to I Feel You, {user.username}! 💙')
            return redirect('feelings:feed')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    posts = Post.objects.filter(user=user).select_related('user')
    
    context = {
        'profile_user': user,
        'profile': profile,
        'posts': posts,
        'is_own_profile': request.user == user,
    }
    return render(request, 'feelings/profile.html', context)

@login_required
def edit_profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated! ✨')
            return redirect('feelings:profile', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'feelings/edit_profile.html', {'form': form})
