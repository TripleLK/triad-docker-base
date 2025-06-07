from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import LabEquipmentPage, EquipmentModel, QuoteCartItem, QuoteRequest
import json
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

def get_session_key(request):
    """Helper to get or create a session key."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def cart_add(request):
    """Add an item to the quote cart."""
    if request.method == 'POST':
        session_key = get_session_key(request)
        
        # Get parameters from POST data
        equipment_page_id = request.POST.get('equipment_page_id')
        equipment_model_id = request.POST.get('equipment_model_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate that the equipment page exists
        try:
            equipment_page = LabEquipmentPage.objects.get(id=equipment_page_id)
        except LabEquipmentPage.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Equipment not found'})
        
        # Get model details
        if equipment_model_id:
            try:
                equipment_model = EquipmentModel.objects.get(id=equipment_model_id)
                model_name = equipment_model.name
                model_number = equipment_model.model_number
            except EquipmentModel.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Model not found'})
        else:
            # If no model is specified, use the equipment page details
            model_name = equipment_page.title
            model_number = "N/A"
        
        # Check if item already exists in cart
        existing_item = QuoteCartItem.objects.filter(
            session_key=session_key,
            equipment_page_id=equipment_page_id,
            equipment_model_id=equipment_model_id
        ).first()
        
        if existing_item:
            # Just set the quantity rather than incrementing it
            existing_item.quantity = quantity
            existing_item.save()
            message = f'Updated quantity for {model_name}'
        else:
            # Create new cart item
            QuoteCartItem.objects.create(
                session_key=session_key,
                equipment_page_id=equipment_page_id,
                equipment_model_id=equipment_model_id,
                model_name=model_name,
                model_number=model_number,
                quantity=quantity
            )
            message = f'{model_name} added to your quote cart'
        
        # Get cart count for the response
        cart_count_result = QuoteCartItem.objects.filter(session_key=session_key).aggregate(
            total_items=Sum('quantity')
        )
        cart_count = cart_count_result['total_items'] or 0
        
        return JsonResponse({
            'success': True, 
            'message': message,
            'cart_count': cart_count
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def cart_update(request):
    """Update the quantity of an item in the cart."""
    if request.method == 'POST':
        session_key = get_session_key(request)
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            cart_item = QuoteCartItem.objects.get(id=item_id, session_key=session_key)
            
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                message = 'Quantity updated'
            else:
                # Delete item if quantity is 0
                cart_item.delete()
                message = 'Item removed from cart'
            
            # Get current cart count
            cart_count_result = QuoteCartItem.objects.filter(session_key=session_key).aggregate(
                total_items=Sum('quantity')
            )
            cart_count = cart_count_result['total_items'] or 0
            
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_count': cart_count
            })
                
        except QuoteCartItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Item not found in your cart'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def cart_remove(request, item_id):
    """Remove an item from the cart."""
    session_key = get_session_key(request)
    
    try:
        cart_item = QuoteCartItem.objects.get(id=item_id, session_key=session_key)
        cart_item.delete()
        messages.success(request, 'Item removed from your quote cart')
    except QuoteCartItem.DoesNotExist:
        messages.error(request, 'Item not found in your cart')
    
    return HttpResponseRedirect(reverse('cart_view'))

def cart_view(request):
    """Display the quote cart contents."""
    session_key = get_session_key(request)
    cart_items = QuoteCartItem.objects.filter(session_key=session_key)
    
    # Get total items count
    cart_count_result = cart_items.aggregate(total_items=Sum('quantity'))
    cart_count = cart_count_result['total_items'] or 0
    
    context = {
        'cart_items': cart_items,
        'cart_count': cart_count
    }
    
    return render(request, 'base_site/quote_cart.html', context)

def quote_request_form(request):
    """
    Display and process the quote request form.
    Can be used for both cart-based quotes and individual product quotes.
    """
    session_key = get_session_key(request)
    
    # For single product quotes (when not using the cart)
    equipment_page_id = request.GET.get('equipment_page_id')
    equipment_model_id = request.GET.get('equipment_model_id')
    single_product = None
    single_model = None
    
    # Only get cart items if we're not requesting a quote for a specific product
    if equipment_page_id:
        try:
            single_product = LabEquipmentPage.objects.get(id=equipment_page_id)
            if equipment_model_id:
                try:
                    single_model = EquipmentModel.objects.get(id=equipment_model_id)
                except EquipmentModel.DoesNotExist:
                    pass
            # Don't show cart items when requesting a single product quote
            cart_items = []
        except LabEquipmentPage.DoesNotExist:
            # If the product doesn't exist, show normal cart
            cart_items = QuoteCartItem.objects.filter(session_key=session_key)
    else:
        # Normal quote cart request
        cart_items = QuoteCartItem.objects.filter(session_key=session_key)
    
    if request.method == 'POST':
        # Process form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        company = request.POST.get('company', '')
        inquiry_type = request.POST.get('inquiry_type')
        message = request.POST.get('message')
        
        # Basic validation
        if not name or not email or not message:
            messages.error(request, 'Please fill in all required fields')
            return render(request, 'base_site/quote_request_form.html', {
                'cart_items': cart_items,
                'single_product': single_product,
                'single_model': single_model
            })
        
        # Create the quote request
        quote_request = QuoteRequest.objects.create(
            name=name,
            email=email,
            phone=phone,
            company=company,
            inquiry_type=inquiry_type,
            message=message,
            session_key=session_key
        )
        
        # If it's a single product quote (not from cart), create a cart item
        if single_product and not cart_items:
            model_name = single_model.name if single_model else single_product.title
            model_number = single_model.model_number if single_model else "N/A"
            
            QuoteCartItem.objects.create(
                session_key=session_key,
                equipment_page_id=single_product.id,
                equipment_model_id=single_model.id if single_model else None,
                model_name=model_name,
                model_number=model_number,
                quantity=1
            )
        
        # Add a success message
        messages.success(request, 'Your quote request has been submitted successfully!')
        
        # Redirect to success page or back to products
        return redirect('quote_request_success')
    
    # GET request - show the form
    context = {
        'cart_items': cart_items,
        'single_product': single_product,
        'single_model': single_model
    }
    
    return render(request, 'base_site/quote_request_form.html', context)

def quote_request_success(request):
    """Display a success page after submitting a quote request."""
    return render(request, 'base_site/quote_request_success.html')

def request_single_quote(request, equipment_page_id, equipment_model_id=None):
    """Shortcut view to request a quote for a single product."""
    # Redirect to the quote request form with product parameters
    url = reverse('quote_request_form')
    if equipment_model_id:
        url += f'?equipment_page_id={equipment_page_id}&equipment_model_id={equipment_model_id}'
    else:
        url += f'?equipment_page_id={equipment_page_id}'
    
    return redirect(url)

def get_cart_items(request):
    """Get all cart items for the current session."""
    session_key = get_session_key(request)
    cart_items = QuoteCartItem.objects.filter(session_key=session_key)
    
    # Format cart items for JSON response
    cart_items_data = []
    for item in cart_items:
        try:
            equipment_page = LabEquipmentPage.objects.get(id=item.equipment_page_id)
            page_slug = equipment_page.slug
        except LabEquipmentPage.DoesNotExist:
            page_slug = ""
            
        cart_items_data.append({
            'id': item.id,
            'equipment_page_id': item.equipment_page_id,
            'equipment_model_id': item.equipment_model_id,
            'model_name': item.model_name,
            'model_number': item.model_number,
            'quantity': item.quantity,
            'page_slug': page_slug
        })
    
    return JsonResponse({
        'success': True,
        'cart_items': cart_items_data
    })

def cart_remove_item(request):
    """Remove an item from the cart via AJAX."""
    if request.method == 'POST':
        session_key = get_session_key(request)
        equipment_page_id = request.POST.get('equipment_page_id')
        equipment_model_id = request.POST.get('equipment_model_id')
        
        # Filter conditions
        filter_kwargs = {
            'session_key': session_key,
            'equipment_page_id': equipment_page_id
        }
        
        if equipment_model_id:
            filter_kwargs['equipment_model_id'] = equipment_model_id
        else:
            filter_kwargs['equipment_model_id__isnull'] = True
        
        # Delete matching items
        QuoteCartItem.objects.filter(**filter_kwargs).delete()
        
        # Get updated cart count
        cart_count_result = QuoteCartItem.objects.filter(session_key=session_key).aggregate(
            total_items=Sum('quantity')
        )
        cart_count = cart_count_result['total_items'] or 0
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': cart_count
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@staff_member_required
def human_review_queue(request):
    """
    Display a queue of lab equipment pages that need human review.
    Only accessible to staff members.
    """
    items_to_review = LabEquipmentPage.objects.filter(needs_review=True).order_by('-last_published_at')
    
    context = {
        'items': items_to_review,
        'page_title': 'Human Review Queue',
    }
    
    return render(request, 'base_site/human_review_queue.html', context) 