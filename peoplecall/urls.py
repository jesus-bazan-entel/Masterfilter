from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

urlpatterns = [
    path('', peoplecall, name="peoplecall"),
    path('upload', upload, name="upload"),
    path('reanude', reanude, name="reanude"),
    path('export', export, name="export"),
    path('process/', process, name="process"),
    path('consult/', consult, name="consult"),
    path('filter_data/', filter_data, name="filter_data"),
    path('pause/', pause, name="pause"),
    path('remove/', remove, name="remove"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)