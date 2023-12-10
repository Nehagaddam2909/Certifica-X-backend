from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("sendMails/", views.send_pdf_to_emails),
    path("decryptQR/", views.decrypt_qr_code),

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
