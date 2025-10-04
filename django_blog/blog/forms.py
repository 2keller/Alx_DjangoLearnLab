from django import forms
from .models import Post, Comment
from taggit.forms import TagWidget

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'tags']
        tags = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Add tags separated by commas'}),
        help_text="Separate tags with commas"
        widgets = {
            'tags': TagWidget(attrs={'placeholder': 'Add tags separated by commas'}),
        }
    )

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

