# views.py
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import PDFUpload
from .serializers import PDFUploadSerializer
from .utils import get_stock_json  # Import extraction function

# Set up logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
def pdf_upload(request):
    """
    Handle file upload and automatic JSON extraction.
    """
    if request.method == 'POST':
        file = request.FILES.get('file')  # Retrieve the file from the request
        if file:
            # Save the uploaded PDF file
            pdf_upload = PDFUpload(file=file)
            pdf_upload.save()  # Save file and trigger extraction

            # Log the saved data
            logger.debug("PDF Uploaded: %s", pdf_upload.file.name)

            # Return the uploaded PDF details and extracted data
            serializer = PDFUploadSerializer(pdf_upload)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_extracted_data(request, pk):
    """
    Fetch the extracted data for a specific PDF by its ID.
    """
    try:
        pdf = PDFUpload.objects.get(pk=pk)  # Retrieve the PDFUpload instance by ID
        return Response(pdf.extracted_data, status=status.HTTP_200_OK)  # Return the extracted data
    except PDFUpload.DoesNotExist:
        return Response({'error': 'PDF not found'}, status=status.HTTP_404_NOT_FOUND)
