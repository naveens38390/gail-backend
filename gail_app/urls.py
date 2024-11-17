# gail_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('pdf/upload/', views.pdf_upload, name='pdf-upload'),  # POST request to upload PDFs
    path('pdf/<int:pk>/data/', views.get_extracted_data, name='get-extracted-data'),  # GET request to fetch extracted data
]
