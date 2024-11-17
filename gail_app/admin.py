# admin.py
from django.contrib import admin
from .models import PDFUpload

@admin.register(PDFUpload)
class PDFUploadAdmin(admin.ModelAdmin):
    list_display = ('id','file', 'uploaded_at', 'extracted_data')  # Show file, upload time, and extracted data in the list
    search_fields = ('file',)  # Search by file name
