from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import PDFUpload, ExcelUpload, CrossReference
from .serializers import (
    PDFUploadSerializer, 
    ExcelUploadSerializer, 
    CrossReferenceSerializer,
    CrossReferenceQuerySerializer,
    CrossReferenceResponseSerializer
)
from .utils import save_cross_reference_to_db

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

@api_view(['POST'])
def excel_upload(request):
    """
    Handle Excel file upload and automatic data extraction.
    """
    if request.method == 'POST':
        file = request.FILES.get('file')
        file_type = request.data.get('file_type', 'cross_reference')
        is_active = request.data.get('is_active', True)

        if file:
            # Validate file extension
            allowed_extensions = ['.xlsx', '.xls', '.csv']
            file_ext = file.name.lower().split('.')[-1]
            if f'.{file_ext}' not in allowed_extensions:
                return Response({
                    'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            excel_upload = ExcelUpload(
                file=file, 
                file_type=file_type,
                is_active=is_active
            )
            excel_upload.save()  # Save file and trigger extraction
            
            # Save cross-reference data to database for faster querying
            if file_type == 'cross_reference' and excel_upload.extracted_data:
                save_cross_reference_to_db(excel_upload)

            serializer = ExcelUploadSerializer(excel_upload)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Missing file'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_locations(request):
    """
    Get all available locations from the most recent stock point or ex-work files.
    """
    try:
        # Get the most recent stock point file
        stock_point_file = PDFUpload.objects.filter(
            file_type='stock_point_file',
            extracted_data__isnull=False
        ).order_by('-uploaded_at').first()
        
        # Get the most recent ex-work file
        ex_work_file = PDFUpload.objects.filter(
            file_type='ex_work_file',
            extracted_data__isnull=False
        ).order_by('-uploaded_at').first()
        
        locations = set()
        
        # Extract locations from stock point file
        if stock_point_file and stock_point_file.extracted_data:
            for item in stock_point_file.extracted_data.get('data', []):
                if item.get('location'):
                    locations.add(item['location'])
        
        # Extract locations from ex-work file
        if ex_work_file and ex_work_file.extracted_data:
            for item in ex_work_file.extracted_data.get('data', []):
                location = item.get('location') or item.get('location_grade')
                if location:
                    locations.add(location)
        
        locations_list = sorted(list(locations))
        
        return Response({
            'locations': locations_list,
            'total_locations': len(locations_list),
            'source_files': {
                'stock_point': stock_point_file.id if stock_point_file else None,
                'ex_work': ex_work_file.id if ex_work_file else None
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_grades_by_location(request):
    """
    Get all available product grades for a specific location.
    """
    location = request.query_params.get('location')
    
    if not location:
        return Response({'error': 'location parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get the most recent stock point and ex-work files
        stock_point_file = PDFUpload.objects.filter(
            file_type='stock_point_file',
            extracted_data__isnull=False
        ).order_by('-uploaded_at').first()
        
        ex_work_file = PDFUpload.objects.filter(
            file_type='ex_work_file',
            extracted_data__isnull=False
        ).order_by('-uploaded_at').first()
        
        grades = set()
        location_data = []
        
        # Extract grades from stock point file for the specific location
        if stock_point_file and stock_point_file.extracted_data:
            for item in stock_point_file.extracted_data.get('data', []):
                if item.get('location', '').strip().lower() == location.strip().lower():
                    location_data.append({
                        'sap_code': item.get('sap_code'),
                        'location': item.get('location'),
                        'file_type': 'stock_point',
                        'products': item.get('products', [])
                    })
                    # Extract product codes (grades)
                    for product in item.get('products', []):
                        if product.get('product_code'):
                            grades.add(product['product_code'])
        
        # Extract grades from ex-work file for the specific location
        if ex_work_file and ex_work_file.extracted_data:
            for item in ex_work_file.extracted_data.get('data', []):
                item_location = item.get('location') or item.get('location_grade')
                if item_location and item_location.strip().lower() == location.strip().lower():
                    location_data.append({
                        'sap_code': item.get('sap_code'),
                        'location': item_location,
                        'file_type': 'ex_work',
                        'products': item.get('products', [])
                    })
                    # Extract product codes (grades)
                    for product in item.get('products', []):
                        if product.get('product_code'):
                            grades.add(product['product_code'])
        
        grades_list = sorted(list(grades))
        
        return Response({
            'location': location,
            'grades': grades_list,
            'total_grades': len(grades_list),
            'location_data': location_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def cross_reference_by_location(request):
    """
    Query cross-reference data based on location, grade (product code), and competitor.
    
    Query parameters:
    - location: Location from stock point/ex-work files (optional)
    - grade: Product code (GAIL Grade from cross-reference file) (required)
    - competitor: Competitor company name (required)
    """
    location = request.query_params.get('location')
    grade = request.query_params.get('grade')  # This is the product code like B56A003A
    competitor = request.query_params.get('competitor')
    
    if not all([grade, competitor]):
        return Response({
            'error': 'grade (product code) and competitor are required parameters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Query cross-reference data for the product code and competitor
        cross_references = CrossReference.objects.filter(
            gail_grade__iexact=grade.strip(),
            competitor_name__iexact=competitor.strip(),
            excel_upload__is_active=True
        ).exclude(
            competitor_grade__iexact='No equivalent'
        ).exclude(
            competitor_grade__isnull=True
        ).exclude(
            competitor_grade__exact=''
        ).exclude(
            competitor_grade__iexact='(blank)'
        ).distinct()
        
        if not cross_references.exists():
            # Try fuzzy matching for grade
            cross_references = CrossReference.objects.filter(
                gail_grade__icontains=grade.strip(),
                competitor_name__iexact=competitor.strip(),
                excel_upload__is_active=True
            ).exclude(
                competitor_grade__iexact='No equivalent'
            ).exclude(
                competitor_grade__isnull=True
            ).exclude(
                competitor_grade__exact=''
            ).exclude(
                competitor_grade__iexact='(blank)'
            ).distinct()
        
        if cross_references.exists():
            equivalent_grades = list(cross_references.values_list('competitor_grade', flat=True))
            
            # Get additional information about the location and grade if location provided
            location_info = None
            location_available = False
            if location:
                location_info = get_location_info_internal(location, grade)
                location_available = bool(location_info['stock_point_data'] or location_info['ex_work_data'])
            
            response_data = {
                'location': location,
                'gail_grade': grade,
                'competitor_name': competitor,
                'equivalent_grades': equivalent_grades,
                'total_matches': len(equivalent_grades),
                'location_available': location_available
            }
            
            if location_info:
                response_data['location_info'] = location_info
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'No equivalent grades found for this combination',
                'location': location,
                'gail_grade': grade,
                'competitor_name': competitor,
                'equivalent_grades': [],
                'total_matches': 0,
                'available_competitors': get_available_competitors_for_grade(grade)
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_competitors_for_grade(request):
    """
    Get list of competitors that have valid mappings for a specific GAIL grade (product code).
    """
    grade = request.query_params.get('grade')
    
    if not grade:
        return Response({'error': 'grade parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get competitors that have valid mappings for this grade
        competitors = CrossReference.objects.filter(
            gail_grade__iexact=grade.strip(),
            excel_upload__is_active=True
        ).exclude(
            competitor_grade__iexact='No equivalent'
        ).exclude(
            competitor_grade__isnull=True
        ).exclude(
            competitor_grade__exact=''
        ).exclude(
            competitor_grade__iexact='(blank)'
        ).values_list('competitor_name', flat=True).distinct()
        
        if not competitors:
            # Try fuzzy matching
            competitors = CrossReference.objects.filter(
                gail_grade__icontains=grade.strip(),
                excel_upload__is_active=True
            ).exclude(
                competitor_grade__iexact='No equivalent'
            ).exclude(
                competitor_grade__isnull=True
            ).exclude(
                competitor_grade__exact=''
            ).exclude(
                competitor_grade__iexact='(blank)'
            ).values_list('competitor_name', flat=True).distinct()
        
        competitors_list = list(competitors)
        
        return Response({
            'grade': grade,
            'competitors': competitors_list,
            'total_competitors': len(competitors_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_available_competitors_for_grade(grade):
    """
    Internal helper function to get available competitors for a grade
    """
    try:
        competitors = CrossReference.objects.filter(
            gail_grade__iexact=grade.strip(),
            excel_upload__is_active=True
        ).exclude(
            competitor_grade__iexact='No equivalent'
        ).exclude(
            competitor_grade__isnull=True
        ).exclude(
            competitor_grade__exact=''
        ).exclude(
            competitor_grade__iexact='(blank)'
        ).values_list('competitor_name', flat=True).distinct()
        
        return list(competitors)
    except:
        return []

@api_view(['GET'])
def get_all_product_codes(request):
    """
    Get all available GAIL product codes that have cross-reference mappings.
    """
    try:
        # Get all GAIL grades (product codes) that have at least one valid mapping
        product_codes = CrossReference.objects.filter(
            excel_upload__is_active=True
        ).exclude(
            competitor_grade__iexact='No equivalent'
        ).exclude(
            competitor_grade__isnull=True
        ).exclude(
            competitor_grade__exact=''
        ).exclude(
            competitor_grade__iexact='(blank)'
        ).values_list('gail_grade', flat=True).distinct()
        
        product_codes_list = sorted(list(product_codes))
        
        return Response({
            'product_codes': product_codes_list,
            'total_codes': len(product_codes_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])  
def get_cross_reference_summary(request):
    """
    Get a summary of cross-reference data for a specific product code.
    Shows all competitor mappings for a given GAIL grade.
    """
    grade = request.query_params.get('grade')
    
    if not grade:
        return Response({'error': 'grade parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get all mappings for this grade
        cross_references = CrossReference.objects.filter(
            gail_grade__iexact=grade.strip(),
            excel_upload__is_active=True
        ).values('competitor_name', 'competitor_grade').distinct()
        
        if not cross_references:
            return Response({
                'message': 'No cross-reference data found for this product code',
                'gail_grade': grade,
                'mappings': {}
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Organize data by competitor
        mappings = {}
        for ref in cross_references:
            competitor = ref['competitor_name']
            grade_mapping = ref['competitor_grade']
            
            if competitor not in mappings:
                mappings[competitor] = []
            
            # Only add valid mappings (not "No equivalent" or empty)
            if (grade_mapping and 
                grade_mapping.strip() and 
                grade_mapping.lower() not in ['no equivalent', '(blank)', 'null', '']):
                mappings[competitor].append(grade_mapping)
        
        # Remove competitors with no valid mappings
        mappings = {k: v for k, v in mappings.items() if v}
        
        return Response({
            'gail_grade': grade,
            'mappings': mappings,
            'total_competitors': len(mappings)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_grades_for_location_internal(location):
    """
    Internal function to get grades available at a specific location.
    """
    grades = set()
    
    # Get the most recent files
    stock_point_file = PDFUpload.objects.filter(
        file_type='stock_point_file',
        extracted_data__isnull=False
    ).order_by('-uploaded_at').first()
    
    ex_work_file = PDFUpload.objects.filter(
        file_type='ex_work_file',
        extracted_data__isnull=False
    ).order_by('-uploaded_at').first()
    
    # Extract grades from stock point file
    if stock_point_file and stock_point_file.extracted_data:
        for item in stock_point_file.extracted_data.get('data', []):
            if item.get('location', '').strip().lower() == location.strip().lower():
                for product in item.get('products', []):
                    if product.get('product_code'):
                        grades.add(product['product_code'])
    
    # Extract grades from ex-work file
    if ex_work_file and ex_work_file.extracted_data:
        for item in ex_work_file.extracted_data.get('data', []):
            item_location = item.get('location') or item.get('location_grade')
            if item_location and item_location.strip().lower() == location.strip().lower():
                for product in item.get('products', []):
                    if product.get('product_code'):
                        grades.add(product['product_code'])
    
    return sorted(list(grades))

def get_location_info_internal(location, grade):
    """
    Internal function to get detailed information about a location and grade.
    """
    info = {
        'stock_point_data': [],
        'ex_work_data': []
    }
    
    # Get the most recent files
    stock_point_file = PDFUpload.objects.filter(
        file_type='stock_point_file',
        extracted_data__isnull=False
    ).order_by('-uploaded_at').first()
    
    ex_work_file = PDFUpload.objects.filter(
        file_type='ex_work_file',
        extracted_data__isnull=False
    ).order_by('-uploaded_at').first()
    
    # Extract info from stock point file
    if stock_point_file and stock_point_file.extracted_data:
        for item in stock_point_file.extracted_data.get('data', []):
            if item.get('location', '').strip().lower() == location.strip().lower():
                for product in item.get('products', []):
                    if product.get('product_code') == grade:
                        info['stock_point_data'].append({
                            'sap_code': item.get('sap_code'),
                            'price': product.get('price'),
                            'freight_amount': item.get('freight_amount')
                        })
    
    # Extract info from ex-work file
    if ex_work_file and ex_work_file.extracted_data:
        for item in ex_work_file.extracted_data.get('data', []):
            item_location = item.get('location') or item.get('location_grade')
            if item_location and item_location.strip().lower() == location.strip().lower():
                for product in item.get('products', []):
                    if product.get('product_code') == grade:
                        info['ex_work_data'].append({
                            'sap_code': item.get('sap_code'),
                            'price': product.get('price'),
                            'freight_amount': item.get('freight_amount')
                        })
    
    return info

# Keep the existing endpoints for backward compatibility
@api_view(['GET'])
def get_excel_data(request):
    """
    Fetch data from Excel uploads.
    """
    file_type = request.query_params.get('file_type', 'cross_reference')
    upload_id = request.query_params.get('upload_id')
    
    try:
        if upload_id:
            excel_upload = ExcelUpload.objects.get(id=upload_id, file_type=file_type)
        else:
            # Get the most recent active upload of this type
            excel_upload = ExcelUpload.objects.filter(
                file_type=file_type, 
                is_active=True
            ).first()
            
        if not excel_upload:
            return Response({'error': 'No Excel file found'}, status=status.HTTP_404_NOT_FOUND)
            
        return Response(excel_upload.extracted_data, status=status.HTTP_200_OK)
    except ExcelUpload.DoesNotExist:
        return Response({'error': 'Excel file not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def cross_reference_query(request):
    """
    Query cross-reference data to find equivalent grades.
    (Legacy endpoint - maintained for backward compatibility)
    """
    gail_grade = request.query_params.get('gail_grade')
    competitor_name = request.query_params.get('competitor_name')
    location = request.query_params.get('location')
    
    if not gail_grade or not competitor_name:
        return Response({
            'error': 'gail_grade and competitor_name are required parameters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Build query
    query = Q(gail_grade__iexact=gail_grade) & Q(competitor_name__iexact=competitor_name)
    
    # Get active cross-references and exclude invalid entries
    cross_references = CrossReference.objects.filter(
        query,
        excel_upload__is_active=True
    ).exclude(
        competitor_grade__iexact='No equivalent'
    ).exclude(
        competitor_grade__isnull=True
    ).exclude(
        competitor_grade__exact=''
    ).exclude(
        competitor_grade__iexact='(blank)'
    ).distinct()
    
    if not cross_references.exists():
        # Try fuzzy matching for GAIL grade
        fuzzy_query = Q(gail_grade__icontains=gail_grade) & Q(competitor_name__iexact=competitor_name)
        
        cross_references = CrossReference.objects.filter(
            fuzzy_query,
            excel_upload__is_active=True
        ).exclude(
            competitor_grade__iexact='No equivalent'
        ).exclude(
            competitor_grade__isnull=True
        ).exclude(
            competitor_grade__exact=''
        ).exclude(
            competitor_grade__iexact='(blank)'
        ).distinct()
    
    if cross_references.exists():
        equivalent_grades = list(cross_references.values_list('competitor_grade', flat=True))
        
        response_data = {
            'gail_grade': gail_grade,
            'competitor_name': competitor_name,
            'equivalent_grades': equivalent_grades,
            'total_matches': len(equivalent_grades)
        }
        
        if location:
            response_data['location'] = location
            
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response({
            'message': 'No equivalent grades found',
            'gail_grade': gail_grade,
            'competitor_name': competitor_name,
            'equivalent_grades': [],
            'total_matches': 0
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_companies_list(request):
    """
    Get list of all competitor companies in the active cross-reference data.
    """
    try:
        # Get active cross-reference upload
        active_upload = ExcelUpload.objects.filter(
            file_type='cross_reference',
            is_active=True
        ).first()
        
        if not active_upload or not active_upload.extracted_data:
            return Response({'error': 'No active cross-reference data found'}, status=status.HTTP_404_NOT_FOUND)
        
        companies = active_upload.extracted_data.get('companies', [])
        
        return Response({
            'companies': companies,
            'total_companies': len(companies)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_gail_grades_list(request):
    """
    Get list of all GAIL grades in the active cross-reference data.
    """
    try:
        # Get from database for faster access
        gail_grades = CrossReference.objects.filter(
            excel_upload__is_active=True
        ).values_list('gail_grade', flat=True).distinct()
        
        gail_grades_list = sorted(list(gail_grades))
        
        return Response({
            'gail_grades': gail_grades_list,
            'total_grades': len(gail_grades_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def search_cross_reference(request):
    """
    Advanced search for cross-reference data with multiple filters.
    """
    # Get query parameters
    gail_grade = request.query_params.get('gail_grade')
    competitor_name = request.query_params.get('competitor_name')
    competitor_grade = request.query_params.get('competitor_grade')
    location = request.query_params.get('location')
    
    # Build query
    query = Q(excel_upload__is_active=True)
    
    if gail_grade:
        query &= Q(gail_grade__icontains=gail_grade)
    if competitor_name:
        query &= Q(competitor_name__icontains=competitor_name)
    if competitor_grade:
        query &= Q(competitor_grade__icontains=competitor_grade)
    if location:
        query &= Q(location__icontains=location)
    
    # Execute query
    cross_references = CrossReference.objects.filter(query)[:100]  # Limit to 100 results
    
    # Serialize results
    serializer = CrossReferenceSerializer(cross_references, many=True)
    
    return Response({
        'results': serializer.data,
        'total_results': len(serializer.data),
        'filters_applied': {
            'gail_grade': gail_grade,
            'competitor_name': competitor_name,
            'competitor_grade': competitor_grade,
            'location': location
        }
    }, status=status.HTTP_200_OK)


# Add this function to your views.py file (anywhere after the imports)

@api_view(['GET'])
def cross_reference_with_competitor_pricing(request):
    """
    Get competitor grades with their actual prices at specified location.
    
    Query parameters:
    - location: Location name (required)
    - gail_grade: GAIL product code (required) 
    - file_source: 'stock_point' or 'ex_work' (optional, defaults to 'stock_point')
    - competitor: Specific competitor (optional, returns all if not specified)
    """
    location = request.query_params.get('location')
    gail_grade = request.query_params.get('gail_grade')
    file_source = request.query_params.get('file_source', 'stock_point')
    competitor_filter = request.query_params.get('competitor')
    
    if not all([location, gail_grade]):
        return Response({
            'error': 'location and gail_grade are required parameters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Step 1: Get cross-reference data (GAIL grade → competitor grades)
        cross_references = CrossReference.objects.filter(
            gail_grade__iexact=gail_grade.strip(),
            excel_upload__is_active=True
        ).exclude(
            competitor_grade__iexact='No equivalent'
        ).exclude(
            competitor_grade__isnull=True
        ).exclude(
            competitor_grade__exact=''
        ).exclude(
            competitor_grade__iexact='(blank)'
        )
        
        if competitor_filter:
            cross_references = cross_references.filter(competitor_name__iexact=competitor_filter.strip())
        
        if not cross_references.exists():
            return Response({
                'error': 'No cross-reference data found',
                'message': f'No competitor grades found for GAIL grade {gail_grade}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Step 2: Get pricing data from stock point or ex work files
        file_type = 'stock_point_file' if file_source == 'stock_point' else 'ex_work_file'
        
        pricing_file = PDFUpload.objects.filter(
            file_type=file_type,
            extracted_data__isnull=False
        ).order_by('-uploaded_at').first()
        
        if not pricing_file or 'error' in pricing_file.extracted_data:
            return Response({
                'error': f'No valid {file_source} pricing data found',
                'suggestion': f'Please upload a valid {file_type} PDF first'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Step 3: Find location data
        location_data = None
        for item in pricing_file.extracted_data.get('data', []):
            item_location = item.get('location') or item.get('location_grade', '')
            if item_location.strip().lower() == location.strip().lower():
                location_data = item
                break
        
        if not location_data:
            return Response({
                'error': f'Location "{location}" not found in {file_source} data',
                'available_locations': [
                    item.get('location') or item.get('location_grade', '') 
                    for item in pricing_file.extracted_data.get('data', [])
                ]
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Step 4: Build response with competitor grades and their prices
        competitors_with_pricing = []
        
        for ref in cross_references:
            competitor_grade = ref.competitor_grade.strip()
            
            # Find the price of this competitor grade at the location
            competitor_price = None
            for product in location_data.get('products', []):
                if product.get('product_code', '').strip().lower() == competitor_grade.lower():
                    competitor_price = product.get('price')
                    break
            
            competitor_info = {
                'competitor_name': ref.competitor_name,
                'competitor_grade': competitor_grade,
                'competitor_price': competitor_price,
                'competitor_price_formatted': f'₹{competitor_price:,}' if competitor_price else 'Price not available',
                'price_available': competitor_price is not None,
                'gail_grade': ref.gail_grade
            }
            
            competitors_with_pricing.append(competitor_info)
        
        # Step 5: Summary statistics
        available_prices = [comp for comp in competitors_with_pricing if comp['price_available']]
        prices = [comp['competitor_price'] for comp in available_prices]
        
        summary = {
            'location': location,
            'gail_grade': gail_grade,
            'file_source': file_source,
            'total_competitors': len(competitors_with_pricing),
            'competitors_with_prices': len(available_prices),
            'competitors_without_prices': len(competitors_with_pricing) - len(available_prices),
            'price_range': {
                'min_price': min(prices) if prices else None,
                'max_price': max(prices) if prices else None,
                'avg_price': round(sum(prices) / len(prices)) if prices else None
            } if prices else None
        }
        
        response_data = {
            'location': location,
            'gail_grade': gail_grade,
            'file_source': file_source,
            'competitors': competitors_with_pricing,
            'summary': summary,
            'location_info': {
                'sap_code': location_data.get('sap_code'),
                'freight_amount': location_data.get('freight_amount'),
                'total_products_at_location': len(location_data.get('products', []))
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)