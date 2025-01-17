from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.urls import reverse_lazy, reverse
from django.http import Http404


from .models import Post, Category, Comment
from .forms import PostForm, CommentForms

from datetime import datetime

POSTS_VALUE = 5
User = get_user_model()


def date_now():
    return datetime.now()


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        if self.request.user.is_authenticated:
            object = self.get_object()
            return object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', pk=self.kwargs['pk'])


class OnlyUserMixin(UserPassesTestMixin):

    def get_object(self):
        obj = get_object_or_404(User, username=self.kwargs['username'])
        return obj

    def test_func(self):
        if self.request.user.is_authenticated:
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
        if self.request.user.is_authenticated:
            username = self.request.user.username
            return reverse('blog:profile', kwargs={'username': username})
        else:
            return None


class CustomProfileLogin(SuccessReverseProfile, LoginView):
    template_name = 'registration/login.html'


class PostListView(ListViewMixin, ListView):
    """Класс, отображающий главную страницу проекта с постами"""

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
    """Класс, отображающий отдельную страницу с выбранной категорией"""

    template_name = 'blog/category.html'

    def get_context_data(self, **kwargs):
        category = get_object_or_404(
            Category, slug=self.kwargs['slug'],
            is_published=True
        )
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
    """Класс, обрабатывающий страницу создания поста"""

    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(PostCreateView, self).form_valid(form)


class PostDetailView(DetailView):
    """Класс, отображающий страницу отдельного поста"""

    model = Post
    template_name = 'blog/detail.html'

    def get_object(self):
        pk = self.kwargs['pk']
        post = get_object_or_404(Post, id=pk)
        if not (post.is_published or post.author == self.request.user):
            raise Http404()
        return post

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)
        post = self.get_object()
        context['form'] = CommentForms()
        context['post'] = post
        context['comments'] = (
            Comment.objects.filter(post=post).order_by('created_at')
        ).select_related('author', 'post')
        return context


class PostUpdateView(OnlyAuthorMixin, PostFormMixin, UpdateView):
    """Класс, который позволяет редактировать пост"""

    template_name = 'blog/create.html'


class PostDeleteView(OnlyAuthorMixin, SuccessReverse, DeleteView):
    """Класс, управляющий удалением постов"""

    model = Post

    def get_object(self):
        obj = get_object_or_404(
            Post,
            pk=self.kwargs['pk']
        )
        return obj


class ProfileListView(ListView):
    """Класс, отображающий страницу профиля"""

    model = User
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_user(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        user = self.get_user()
        context = super(ProfileListView, self).get_context_data(**kwargs)
        context['profile'] = user
        context['post'] = Post.objects.filter(author=user)
        return context

    def get_queryset(self):
        user = self.get_user()
        if self.request.user.is_authenticated:
            if self.request.user.username == user.username:
                return Post.objects.filter(
                    author=user
                ).select_related(
                    'author', 'location', 'category'
                ).prefetch_related('comments')
            else:
                return Post.objects.filter(
                    author=user,
                    is_published=True,
                    category__is_published=True
                ).select_related(
                    'author', 'location', 'category'
                ).prefetch_related('comments')
        else:
            return Post.objects.filter(
                author=user,
                is_published=True,
                category__is_published=True
            ).select_related(
                'author', 'location', 'category'
            ).prefetch_related('comments')


class ProfileCreateView(SuccessReverse, CreateView):
    """Класс, обрабатывающий создание профиля"""

    template_name = 'registration/registration_form.html'
    form_class = UserCreationForm


class ProfileUpdateView(OnlyUserMixin, SuccessReverse, UpdateView):
    """Класс, обрабатывающий редактирование профиля"""

    model = User
    template_name = 'blog/user.html'
    fields = ['username', 'first_name', 'last_name', 'email', ]

    def get_queryset(self):
        user = self.get_object()
        return user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Класс, обрабатывающий создание комментария"""

    object = None
    model = Comment
    form_class = CommentForms

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, pk=kwargs['pk'])
        return super(
            CommentCreateView, self
        ).dispatch(request, *args, **kwargs)

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
    """Класс, обрабатывающий редактирование профиля"""

    fields = ['text', ]


class CommentDeleteView(OnlyAuthorMixin, DeleteView):
    """Класс, обрабатывающий удаление комментария"""

    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self):
        obj = get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post_id=self.kwargs['pk']
        )
        return obj

    def get_context_data(self, **kwargs):
        obj = self.get_object()
        context = super().get_context_data(**kwargs)
        context['comment'] = obj
        if 'form' in context:
            del context['form']
        return context

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.kwargs['pk']})
