# serializers.py
from rest_framework import serializers
from .models import PDFUpload

class PDFUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDFUpload
        fields = ['id', 'file', 'extracted_data', 'uploaded_at']  # Include file, extracted data, and timestamp
