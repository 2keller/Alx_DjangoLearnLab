from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import permission_required

@permission_required('advanced_features_and_security.can_edit', raise_exception=True)
def edit_article(request, article_id):
    # your edit logic here
    return render(request, 'edit_article.html', {'article_id': article_id})