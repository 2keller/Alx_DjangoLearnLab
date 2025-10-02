
    
# In blog/views.py

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import PostForm, CommentForm 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django import forms
from django.contrib.auth.forms import UserCreationForm 
# FIX: Removed the trailing comma (,)
from .models import Profile, Post 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from .models import Comment






class CustomUSerCReationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email") 


# A view to handle registration of new users to the site 
def Register(request):
    if request.method == "POST":
        form = CustomUSerCReationForm(request.POST)
        if form.is_valid():
            user = form.save() 
            # FIX: Removed login(request, user) call. If you redirect to "login", 
            # the user should not be logged in first, as that would immediately log them out.
            Profile.objects.create(user=user)
            
            return redirect("login")
    else:
        form = CustomUSerCReationForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def profile(request):
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


class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    ordering = ['-published_date']


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = Comment.objects.filter(Post=self.kwargs['pk'])
        return context
    
@login_required
def AddComment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.Post = post
            comment.author = request.user
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment.html', {'form': form})



class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_update.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == Post.author
    

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/post_delete.html'
    # FIX: DeleteView requires a success_url to know where to redirect after deletion.
    success_url = '/' 

    def test_func(self):
        post = self.get_object()
        return self.request.user == Post.author
    
class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['Post', 'author', 'content']
    template_name = 'blog/comment_create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment_delete.html'
    # FIX: DeleteView requires a success_url to know where to redirect after deletion.
    success_url = '/' 

    def test_func(self):
        comment = self.get_object()
        return self.request.user == Comment.author

class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    fields = ['Post', 'author', 'content']
    template_name = 'blog/comment_update.html'

    def test_func(self):
        comment = self.get_object()
        return self.request.user == Comment.author
    

class CommentListView(ListView):
    model = Comment
    template_name = 'blog/comment_list.html'
    context_object_name = 'comments'