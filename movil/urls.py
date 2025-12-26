from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

urlpatterns = [
    path('', movil, name="movil"),
    path('login', login, name="login"),
    path('logout', logout, name="logout"),
    path('upload', upload, name="upload"),
    path('reanude', reanude, name="reanude"),
    path('export', export, name="export"),
    path('sign_in_fijo', sign_in_fijo, name="sign_in_fijo"),
    path('consult_individual', consult_individual, name="consult_individual"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)