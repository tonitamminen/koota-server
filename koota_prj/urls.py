"""koota_prj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from kdata import views as kviews

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^login/$', auth_views.login, {'template_name': 'koota/login.html'}),
    url('^', include('django.contrib.auth.urls')),

    url('^post$', kviews.post),
    url('^devices/$', kviews.DeviceListView.as_view(), name='device-list'),
    url('^devices/(?P<id>[0-9a-fA-F]*)/$', kviews.DeviceDetail.as_view(),
        name='device-detail'),
    url('^devices/(?P<id>[0-9a-fA-F]*)/qr.png$', kviews.device_qrcode,
        name='device-qr'),
    url('^devices/create/$', kviews.DeviceCreate.as_view(),
        name='device-create'),


    url('^$', TemplateView.as_view(template_name='koota/main.html')),
    #include('kdata.urls')),
    ]
