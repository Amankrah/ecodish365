from functools import wraps
from rest_framework.response import Response

def seo_metadata(title, description, keywords):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            response = view_func(*args, **kwargs)
            if isinstance(response, Response):
                response.data = {
                    'seo_metadata': {
                        'title': title,
                        'description': description,
                        'keywords': keywords,
                    },
                    'data': response.data
                }
            return response
        return wrapped_view
    return decorator