
from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
import os
from .utils import get_stock_json, add_freight, extract_freight, extract_cross_reference, save_cross_reference_to_db, FILE_TYPE_MAPPING, MONTH_MAPPING

def validate_pdf_file(value):
    """Validate that uploaded file is a PDF"""
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ['.pdf']:
        raise ValidationError('Only PDF files are allowed for PDF uploads.')

def validate_excel_file(value):
    """Validate that uploaded file is an Excel or CSV file"""
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ['.xlsx', '.xls', '.csv']:
        raise ValidationError('Only Excel (.xlsx, .xls) and CSV files are allowed for Excel uploads.')

class PDFUpload(models.Model):
    file = models.FileField(upload_to='pdfs/', validators=[validate_pdf_file])
    extracted_data = models.JSONField(blank=True, null=True)  # Store the extracted data as JSON
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Timestamp for the upload
    file_type = models.CharField(max_length=64, choices=FILE_TYPE_MAPPING.items(), blank=True, null=False)
    month = models.CharField(max_length=64, choices=MONTH_MAPPING.items(), blank=True, null=False)
    year = models.PositiveIntegerField(blank=True, default=date.today().year)

    def clean(self):
        """Additional validation"""
        super().clean()
        if self.file:
            # Check file extension
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext not in ['.pdf']:
                raise ValidationError({'file': 'Only PDF files are allowed for PDF uploads.'})

    def save(self, *args, **kwargs):
        # Check if this is a new object or if we're specifically updating extracted_data
        is_new = self.pk is None
        add_freight_flag = kwargs.pop('add_freight_flag', False)
        update_fields = kwargs.get('update_fields')
        
        # Call the parent save method first
        super().save(*args, **kwargs)

        # Only perform data extraction on new objects and when extracted_data is empty
        if is_new and self.file and not self.extracted_data:
            try:
                if self.file_type == "freight_file":
                    self.extracted_data = extract_freight(self.file.path)  # Extract freight data
                elif self.file_type == "stock_point_file" or self.file_type == "ex_work_file":
                    self.extracted_data = get_stock_json(self.file.path, file_type=self.file_type)  # Extract stock point data
                
                # Save the extracted data using update() to avoid recursion
                if self.extracted_data:
                    PDFUpload.objects.filter(pk=self.pk).update(extracted_data=self.extracted_data)
                    # Refresh the instance
                    self.refresh_from_db()
            except Exception as e:
                print(f"Error extracting data from {self.file.path}: {e}")

        # Check for the presence of all file types of the same month and year
        # Only do this for new uploads, not when updating extracted_data
        if is_new and not add_freight_flag and update_fields != ['extracted_data']:
            same_month_year_files = PDFUpload.objects.filter(month=self.month, year=self.year)
            if same_month_year_files.count() >= 3:
                add_freight(same_month_year_files)

    def __str__(self):
        return f"{self.file_type} - {self.month}/{self.year}"


class ExcelUpload(models.Model):
    """Model for handling Excel file uploads (cross-reference data)"""
    
    EXCEL_FILE_TYPES = [
        ('cross_reference', 'Cross Reference File'),
        # Add more Excel file types as needed
    ]
    
    file = models.FileField(upload_to='excel_files/', validators=[validate_excel_file])
    file_type = models.CharField(max_length=64, choices=EXCEL_FILE_TYPES, default='cross_reference')
    extracted_data = models.JSONField(blank=True, null=True)  # Store extracted data as JSON
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # To manage which cross-reference file is currently active
    
    class Meta:
        ordering = ['-uploaded_at']

    def clean(self):
        """Additional validation"""
        super().clean()
        if self.file:
            # Check file extension
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext not in ['.xlsx', '.xls', '.csv']:
                raise ValidationError({'file': 'Only Excel (.xlsx, .xls) and CSV files are allowed.'})
    
    def save(self, *args, **kwargs):
        # Check if this is a new object
        is_new = self.pk is None
        
        # Call the parent save method first
        super().save(*args, **kwargs)
        
        # Perform data extraction after the record is saved (only for new objects)
        if is_new and self.file and not self.extracted_data:
            try:
                if self.file_type == "cross_reference":
                    self.extracted_data = extract_cross_reference(self.file.path)
                    
                    # Save the extracted data using update() to avoid recursion
                    if self.extracted_data:
                        ExcelUpload.objects.filter(pk=self.pk).update(extracted_data=self.extracted_data)
                        # Refresh the instance
                        self.refresh_from_db()
                    
                        # If this is a new active cross-reference file, deactivate others
                        if self.is_active:
                            ExcelUpload.objects.filter(file_type='cross_reference', is_active=True).exclude(id=self.id).update(is_active=False)
                        
                        # Save cross-reference data to database for faster querying
                        save_cross_reference_to_db(self)
            except Exception as e:
                print(f"Error extracting data from {self.file.path}: {e}")
    
    def __str__(self):
        return f"{self.file_type} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


class CrossReference(models.Model):
    """Model to store individual cross-reference mappings for easier querying"""
    
    gail_grade = models.CharField(max_length=100)  # GAIL's grade
    competitor_name = models.CharField(max_length=100)  # Competitor company name
    competitor_grade = models.CharField(max_length=100)  # Competitor's equivalent grade
    location = models.CharField(max_length=100, blank=True, null=True)  # Location if applicable
    excel_upload = models.ForeignKey(ExcelUpload, on_delete=models.CASCADE, related_name='cross_references')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['gail_grade', 'competitor_name', 'competitor_grade', 'excel_upload']
        indexes = [
            models.Index(fields=['gail_grade', 'competitor_name']),
            models.Index(fields=['competitor_name', 'competitor_grade']),
        ]
    
    def __str__(self):
        return f"{self.gail_grade} -> {self.competitor_name}: {self.competitor_grade}"