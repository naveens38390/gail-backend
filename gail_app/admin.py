from django.contrib import admin
from .models import PDFUpload

@admin.register(PDFUpload)
class PDFUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'file_type', 'month', 'year', 'uploaded_at')  # Display additional fields
    search_fields = ('file', 'file_type', 'month', 'year')  # Allow searching by these fields
