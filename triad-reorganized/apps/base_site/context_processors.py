from django.db.models import Sum
from .models import QuoteCartItem

def quote_cart(request):
    """
    Context processor to add quote cart information to all templates.
    """
    cart_count = 0
    
    if request.session.session_key:
        session_key = request.session.session_key
        # Count total items (sum of quantities) rather than just product count
        cart_count_result = QuoteCartItem.objects.filter(session_key=session_key).aggregate(
            total_items=Sum('quantity')
        )
        cart_count = cart_count_result['total_items'] or 0
    
    return {
        'cart_count': cart_count
    } 