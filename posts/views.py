from urllib.parse import quote_plus

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from comments.models import Comment
from .forms import PostForm
from .models import Post

def post_create(request):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404

    if not request.user.is_authenticated():
        raise Http404

    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.user = request.user
        instance.save()
        # message success
        messages.success(request, "Successfully created")
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "form": form,
    }
    return render(request, "post_form.html", context)

def post_detail(request, slug=None):
    instance = get_object_or_404(Post, slug=slug)
    if instance.publish > timezone.now().date() or instance.draft:
        if not request.user.is_staff or not request.user.is_superuser:
            raise Http404
    share_string = quote_plus(instance.content)
    content_type = ContentType.objects.get_for_model(Post)
    obj_id = instance.id
    #Post.objects.get(id=instance.id)
    comments = Comment.objects.filter(content_type=content_type, object_id=obj_id)

    context = {
        "title": instance.title,
        "instance": instance,
        "share_string": share_string,
        "comments": comments
    }
    return render(request, "post_detail.html", context)

def post_list(request):
    today = timezone.now().date()
    queryset_list = Post.objects.active()
    if request.user.is_staff or request.user.is_superuser:
        queryset_list = Post.objects.all()
    query = request.GET.get("q")
    if query:
        queryset_list = queryset_list.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        ).distinct()
    paginator = Paginator(queryset_list, 3)
    page_request_var = "page"
    page = request.GET.get(page_request_var)
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        queryset = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last pages of results
        queryset = paginator.page(paginator.num_pages)

    context = {
        "objects_list": queryset,
        "title": "List",
        "page_request_var": page_request_var,
        "today": today,
    }
    return render(request, "post_list.html", context)

def post_update(request, slug=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, slug=slug)
    form = PostForm(request.POST or None, request.FILES or None, instance=instance)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        # message success
        messages.success(request, "<a href='#'>Item</a> saved", extra_tags="html_safe")
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "title": instance.title,
        "instance": instance,
        "form": form,
    }
    return render(request, "post_form.html", context)

def post_delete(request, slug=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, slug=slug)
    instance.delete()
    messages.success(request, "Successfully deleted")
    return redirect("posts:list")