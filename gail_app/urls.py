# urls.py (app level)
from django.urls import path
from . import views

urlpatterns = [
    # PDF Upload endpoints (without 'api/' prefix since it's added by main urls.py)
    path('pdf-upload/', views.pdf_upload, name='pdf_upload'),
    
    # Enhanced file data endpoints with freight information
    path('file-data/', views.get_file_data, name='get_file_data'),  # Enhanced with freight
    path('pdf/file-data/', views.get_file_data, name='get_file_data_alt'),  # Alternative path
    
    # New dedicated freight endpoints
    path('freight-data/', views.get_freight_data, name='get_freight_data'),
    # path('comprehensive-pricing/', views.get_comprehensive_pricing_data, name='comprehensive_pricing'),
    
    # Freight debugging and testing endpoints
    path('debug-freight/', views.debug_freight_matching, name='debug_freight_matching'),
    path('freight-coverage-report/', views.get_freight_coverage_report, name='freight_coverage_report'),
    path('test-freight-extraction/', views.test_freight_extraction, name='test_freight_extraction'),
    
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
    path('cross-reference-with-competitor-pricing/', views.cross_reference_with_competitor_pricing, name='cross_reference_with_competitor_pricing'),
    # In urls.py, you can either replace existing URLs or add new ones
    path('enhanced-cross-reference-pricing/', views.enhanced_cross_reference_with_competitor_pricing, name='enhanced_cross_reference_pricing'),
    path('enhanced-competitors-for-grade/', views.enhanced_get_competitors_for_grade, name='enhanced_competitors_for_grade'),
]