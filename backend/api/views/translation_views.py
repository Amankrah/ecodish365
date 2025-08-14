import json
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from dish_cnf_db_pipeline.translator import FrenchTranslator

logger = logging.getLogger(__name__)

french_translator = FrenchTranslator()

def handle_exception(func):
    """Decorator to handle exceptions in views."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in request body")
            return Response({"error": "Invalid JSON in request body"}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return Response({"error": "An unexpected error occurred."}, status=500)
    return wrapper

@api_view(['POST'])
@permission_classes([AllowAny])
@handle_exception
def translate_text(request):
    data = request.data if isinstance(request.data, dict) else {}
    text = data.get('text', '')
    if not text:
        return Response({"error": "No text provided"}, status=400)

    translation = french_translator.translate(text)
    return Response({"translation": translation})