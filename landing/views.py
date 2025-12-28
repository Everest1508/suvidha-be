from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging

logger = logging.getLogger(__name__)


def landing_page(request):
    """Landing page view"""
    return render(request, 'landing/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def contact_form_submit(request):
    """Handle contact form submission"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        # Validate required fields
        if not name or not email or not message:
            return JsonResponse({
                'success': False,
                'error': 'All fields are required.'
            }, status=400)
        
        # Basic email validation
        if '@' not in email:
            return JsonResponse({
                'success': False,
                'error': 'Please enter a valid email address.'
            }, status=400)
        
        # Log the contact form submission (in production, you'd send an email)
        logger.info(f"Contact form submission - Name: {name}, Email: {email}, Message: {message[:100]}...")
        
        # TODO: In production, send an email to admin or save to database
        # For now, we'll just return success
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for contacting us! We will get back to you soon.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again later.'
        }, status=500)
