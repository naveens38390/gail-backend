from rest_framework import serializers
from .models import PDFUpload, ExcelUpload, CrossReference

class PDFUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDFUpload
        fields = ['id', 'file', 'extracted_data', 'uploaded_at', 'file_type', 'month', 'year']

class ExcelUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcelUpload
        fields = ['id', 'file', 'file_type', 'extracted_data', 'uploaded_at', 'is_active']

class CrossReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrossReference
        fields = ['id', 'gail_grade', 'competitor_name', 'competitor_grade', 'location', 'created_at']

class CrossReferenceQuerySerializer(serializers.Serializer):
    """Serializer for cross-reference query parameters"""
    gail_grade = serializers.CharField(max_length=100, help_text="GAIL grade to find equivalents for")
    competitor_name = serializers.CharField(max_length=100, help_text="Competitor company name")
    location = serializers.CharField(max_length=100, required=False, help_text="Location (optional)")

class CrossReferenceResponseSerializer(serializers.Serializer):
    """Serializer for cross-reference response"""
    gail_grade = serializers.CharField()
    competitor_name = serializers.CharField()
    equivalent_grades = serializers.ListField(child=serializers.CharField())
    total_matches = serializers.IntegerField()