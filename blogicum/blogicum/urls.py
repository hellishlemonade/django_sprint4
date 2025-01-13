from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

from blog import views


handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/login/', views.CustomProfileLogin.as_view()),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('blog.urls')),
    path('pages/', include('pages.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
