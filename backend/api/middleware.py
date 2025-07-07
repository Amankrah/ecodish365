import json
from django.http import HttpResponse

class SEOMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if the response is a regular HttpResponse and has a 'data' attribute
        if isinstance(response, HttpResponse) and hasattr(response, 'data'):
            if 'seo_metadata' in response.data:
                metadata = response.data['seo_metadata']
                response['X-Robots-Tag'] = 'index, follow'
                response['Link'] = f'<{request.build_absolute_uri()}>; rel="canonical"'
                
                response.set_cookie('seo_title', metadata['title'])
                response.set_cookie('seo_description', metadata['description'])
                response.set_cookie('seo_keywords', metadata['keywords'])

                # Add structured data if available
                if 'structured_data' in metadata:
                    response['StructuredData'] = json.dumps(metadata['structured_data'])

                # Set cache headers
                response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour

        return response