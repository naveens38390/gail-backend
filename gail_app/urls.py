# gail_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('pdf/upload/', views.pdf_upload, name='pdf-upload'),  # POST request to upload PDFs
    path('pdf/file-data/', views.get_file_data, name='get_file_data'),  # GET request to fetch extracted data
]
