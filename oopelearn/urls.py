from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from courses.views import dashboard

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('exams/', include('exams.urls')),
    re_path(
        r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT},
    ),
]
