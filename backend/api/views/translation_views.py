import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from dish_cnf_db_pipeline.translator import FrenchTranslator
import logging

logger = logging.getLogger(__name__)

french_translator = FrenchTranslator()

def handle_exception(func):
    """Decorator to handle exceptions in views."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in request body")
            return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return JsonResponse({"error": "An unexpected error occurred."}, status=500)
    return wrapper

@csrf_exempt
@require_http_methods(["POST"])
@handle_exception
def translate_text(request):
    data = json.loads(request.body)
    text = data.get('text', '')
    if not text:
        return JsonResponse({"error": "No text provided"}, status=400)
    
    translation = french_translator.translate(text)
    return JsonResponse({"translation": translation})