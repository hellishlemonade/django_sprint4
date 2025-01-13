from django.contrib import admin

from .models import Category, Comment, Location, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'is_published',
        'pub_date',
        'author',
        'category',
        'location',
        'created_at',
    )
    list_editable = (
        'category',
        'is_published',
    )
    search_fields = ('title',)
    list_filter = ('category',)
    list_display_links = ('title',)
    empty_value_display = 'Не задано'


class PostInLine(admin.StackedInline):
    model = Post
    extra = 1


class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInLine,
    )
    list_display = (
        'title',
        'is_published',
        'description',
        'slug',
    )
    list_editable = ('is_published',)
    search_fields = ('title',)
    list_filter = ('slug',)
    list_display_links = ('title',)


class LocationAdmin(admin.ModelAdmin):
    inlines = (
        PostInLine,
    )
    list_display = (
        'name',
        'is_published',
    )
    search_fields = ('name',)
    list_editable = ('is_published',)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'text',
        'post',
        'is_published',
        'author',
        'created_at',
    )
    search_fields = (
        'post',
    )
    list_editable = (
        'is_published',
    )


admin.site.register(Comment, CommentAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Post, PostAdmin)
