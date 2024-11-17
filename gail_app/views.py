from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import PDFUpload
from .serializers import PDFUploadSerializer

@api_view(['POST'])
def pdf_upload(request):
    """
    Handle file upload and automatic JSON extraction.
    """
    if request.method == 'POST':
        file = request.FILES.get('file')  # Retrieve the file from the request
        file_type = request.data.get('file_type')
        month = request.data.get('month')
        year = request.data.get('year')

        if file and file_type and month and year:
            pdf_upload = PDFUpload(file=file, file_type=file_type, month=month, year=year)
            pdf_upload.save()  # Save file and trigger extraction

            serializer = PDFUploadSerializer(pdf_upload)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Missing file, file_type, month, or year'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_file_data(request):
    """
    Fetch data of a specific file type for a given month and year.
    """
    file_type = request.query_params.get('file_type', 'stock_point_file')
    month = request.query_params.get('month')
    year = request.query_params.get('year')

    if not file_type or not month or not year:
        return Response({'error': 'file_type, month, and year are required parameters'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pdf = PDFUpload.objects.get(file_type=file_type, month=month, year=year)
        return Response(pdf.extracted_data, status=status.HTTP_200_OK)
    except PDFUpload.DoesNotExist:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
