"""fornfind URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.flatpages import views
from django.urls import include, path
from django.views.generic.base import RedirectView

from fornfind.settings import ADMIN_PATH


admin.site.site_header = 'FornPunkt administration'
admin.site.site_title = 'FornPunkt administration'

urlpatterns = [
    path(ADMIN_PATH + '/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),

    path('dok/om-fornpunkt/', views.flatpage, {'url': '/dok/om-fornpunkt/'}, name='about'),
    path('dok/andringslogg/', views.flatpage, {'url': '/dok/andringslogg/'}, name='changelog'),
    path('dok/anvandarrattigheter/', views.flatpage, {'url': '/dok/anvandarrattigheter/'}, name='user_rights'),
    path('adm/integritetspolicy/', views.flatpage, {'url': '/adm/integritetspolicy/'}, name='privacy_policy'),
    path('adm/anvandaravtal/', views.flatpage, {'url': '/adm/anvandaravtal/'}, name='user_terms'),
    path('adm/upphovsratt/', views.flatpage, {'url': '/adm/upphovsratt/'}, name='copyright'),
    # this redirect is requried as it was common to link here earlier
    path('andringslogg/', RedirectView.as_view(url='/dok/andringslogg/')),

    path('', include('django.contrib.flatpages.urls')),
]
