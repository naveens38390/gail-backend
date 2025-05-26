# urls.py (app level)
from django.urls import path
from . import views

urlpatterns = [
    # PDF Upload endpoints (without 'api/' prefix since it's added by main urls.py)
    path('pdf-upload/', views.pdf_upload, name='pdf_upload'),
    path('file-data/', views.get_file_data, name='get_file_data'),  # This will be api/file-data/
    path('pdf/file-data/', views.get_file_data, name='get_file_data_alt'),  # This will be api/pdf/file-data/
    
    # Excel Upload endpoints
    path('excel-upload/', views.excel_upload, name='excel_upload'),
    path('excel-data/', views.get_excel_data, name='get_excel_data'),
    
    # Location and Grade endpoints
    path('locations/', views.get_locations, name='get_locations'),
    path('grades-by-location/', views.get_grades_by_location, name='get_grades_by_location'),
    
    # Cross-reference endpoints
    path('cross-reference-by-location/', views.cross_reference_by_location, name='cross_reference_by_location'),
    path('competitors-for-grade/', views.get_competitors_for_grade, name='get_competitors_for_grade'),
    path('cross-reference-summary/', views.get_cross_reference_summary, name='get_cross_reference_summary'),
    path('product-codes/', views.get_all_product_codes, name='get_all_product_codes'),
    
    # Legacy Cross-reference endpoints
    path('cross-reference-query/', views.cross_reference_query, name='cross_reference_query'),
    path('companies-list/', views.get_companies_list, name='get_companies_list'),
    path('gail-grades-list/', views.get_gail_grades_list, name='get_gail_grades_list'),
    path('search-cross-reference/', views.search_cross_reference, name='search_cross_reference'),
]