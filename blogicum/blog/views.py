from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator

from .models import Post, Category, Comment 
from .forms import PostForm, CommentForms

from datetime import datetime

POSTS_VALUE = 5
User = get_user_model()


def date_now():
    return datetime.now()


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', pk=self.kwargs['pk'])


class OnlyUserMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.username == self.request.user.username


class ListViewMixin:
    model = Post
    ordering = '-pub_date'
    paginate_by = 10


class PostFormMixin:
    model = Post
    form_class = PostForm


class CommentMixin:
    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        obj = get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post_id=self.kwargs['pk']
        )
        return obj

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class SuccessReverse:
    success_url = reverse_lazy('blog:index')


class SuccessReverseProfile:

    def get_success_url(self):
        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class CustomProfileLogin(SuccessReverseProfile, LoginView):
    template_name = 'registration/login.html'


class PostListView(ListViewMixin, ListView):
    template_name = 'blog/index.html'
    queryset = Post.objects.filter(
        pub_date__lt=date_now(),
        is_published=True,
        category__is_published=True,
    ).select_related(
        'category',
        'location',
        'author').prefetch_related('comments')


class CategoryListView(ListViewMixin, ListView):
    template_name = 'blog/category.html'

    def get_context_data(self, **kwargs):
        category = get_object_or_404(Category, slug=self.kwargs['slug'])
        context = super(CategoryListView, self).get_context_data(**kwargs)
        context['category'] = category
        return context

    def get_queryset(self):
        slug = self.kwargs['slug']
        return Post.objects.filter(
            pub_date__lt=date_now(),
            is_published=True,
            category__slug=slug,
            category__is_published=True,
        ).select_related(
            'category', 'location', 'author'
        ).prefetch_related('comments')


class PostCreateView(
    LoginRequiredMixin, PostFormMixin, SuccessReverseProfile, CreateView
):
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(PostCreateView, self).form_valid(form)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):
        pk = self.kwargs['pk']
        post = get_object_or_404(Post, id=pk)
        if self.request.user.username != post.author.username:
            obj = get_object_or_404(Post, id=pk, is_published=True)
        else:
            obj = get_object_or_404(Post, id=pk)
        return obj

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)
        context['form'] = CommentForms()
        context['comments'] = (
            self.object.comments.select_related(
                'author'
            ).order_by('-created_at')
        )
        return context


class PostUpdateView(OnlyAuthorMixin, PostFormMixin, UpdateView):
    template_name = 'blog/create.html'


class PostDeleteView(OnlyAuthorMixin, SuccessReverse, DeleteView):
    model = Post

    def get_object(self):
        obj = get_object_or_404(
            Post,
            pk=self.kwargs['pk']
        )
        return obj


class ProfileListView(ListView):
    model = User
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_object(self):
        pass

    def get_context_data(self, **kwargs):
        user = get_object_or_404(User, username=self.kwargs['username'])
        context = super(ProfileListView, self).get_context_data(**kwargs)
        context['profile'] = user
        return context

    def get_queryset(self):
        username = self.kwargs['username']
        author = get_object_or_404(User, username=username)
        if self.request.user.username == username:
            return Post.objects.filter(
                author=author
            ).select_related(
                'category',
                'location',
                'author',
            ).prefetch_related('comments')
        else:
            return Post.objects.filter(
                author=author,
                is_published=True,
                category__is_published=True
            ).select_related(
                'category',
                'location',
                'author',
            ).prefetch_related('comments')


class ProfileCreateView(SuccessReverse, CreateView):
    template_name = 'registration/registration_form.html'
    form_class = UserCreationForm


class ProfileUpdateView(OnlyUserMixin, SuccessReverse, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ['username', 'first_name', 'last_name', 'email',]

    def get_object(self):
        return self.request.user


class CommentCreateView(LoginRequiredMixin, CreateView):
    object = None
    model = Comment
    form_class = CommentForms

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, pk=kwargs['pk'])
        return super(CommentCreateView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        post_id = self.kwargs['pk']
        return Post.objects.get(id=post_id)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.get_object()
        return super(CommentCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})


class CommentUpdateView(OnlyAuthorMixin, CommentMixin, UpdateView):
    fields = ['text',]


class CommentDeleteView(OnlyAuthorMixin, CommentMixin, DeleteView):
    pass
