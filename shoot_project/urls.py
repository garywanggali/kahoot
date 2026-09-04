from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('game.urls')),
]

# django.conf.urls.static.static() is a no-op when DEBUG=False; we always need /media/.
if settings.MEDIA_ROOT:
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': str(settings.MEDIA_ROOT)},
        ),
    ]
