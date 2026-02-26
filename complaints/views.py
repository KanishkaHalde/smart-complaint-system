from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q
from .models import Complaint, ComplaintFile, Notification
import json
import base64
from datetime import timedelta
import uuid

def home(request):
    """Render the main HTML page"""
    return render(request, 'voice_complaint.html')

# ==================== PAGE ROUTES ====================

def login_view(request):
    """Handle login page redirect"""
    return redirect('/')

def register_view(request):
    """Handle register page redirect"""
    return redirect('/')

def logout_view(request):
    """Logout user"""
    logout(request)
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})

# ==================== API ENDPOINTS ====================

@csrf_exempt
def api_login(request):
    """API endpoint for login - FIXED to handle email login"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username_or_email = data.get('username')  # This can be either username or email
            password = data.get('password')
            
            print(f"Login attempt with: {username_or_email}")
            
            user = None
            
            # Try to find user by email first
            try:
                user_obj = User.objects.get(email=username_or_email)
                # Authenticate with username
                user = authenticate(request, username=user_obj.username, password=password)
                print(f"Found user by email: {user_obj.username}")
            except User.DoesNotExist:
                # If not found by email, try as username
                user = authenticate(request, username=username_or_email, password=password)
                print(f"Trying as username: {username_or_email}")
            
            if user is not None:
                login(request, user)
                
                # Create login notification
                Notification.objects.create(
                    user=user,
                    title='Login Successful',
                    message=f'Welcome back {user.username}!',
                    type='success'
                )
                
                return JsonResponse({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_superuser': user.is_superuser,
                        'is_admin': user.is_superuser  # For compatibility with frontend
                    }
                })
            else:
                return JsonResponse({'success': False, 'message': 'Invalid email/username or password'})
        except Exception as e:
            print(f"Login error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def api_register(request):
    """API endpoint for registration - FIXED"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')  # This is name from frontend
            email = data.get('email')
            password = data.get('password')
            
            print(f"Registration attempt - Username: {username}, Email: {email}")
            
            # Validate input
            if not username or not email or not password:
                return JsonResponse({'success': False, 'message': 'All fields are required'})
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'Email already exists'})
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'message': 'Username already exists'})
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            print(f"User created successfully: {user.username}")
            
            # Create welcome notification
            Notification.objects.create(
                user=user,
                title='Welcome!',
                message=f'Welcome {username} to Smart Complaint System!',
                type='success'
            )
            
            # Auto login after registration
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_superuser': user.is_superuser,
                    'is_admin': user.is_superuser  # For compatibility with frontend
                }
            })
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def submit_complaint(request):
    """API endpoint to submit a new complaint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create complaint
            complaint = Complaint.objects.create(
                user=request.user,
                complaint_type=data.get('complaint_type', 'General'),
                urgency=data.get('urgency', 'Normal'),
                location=data.get('location', 'Not specified'),
                details=data.get('details', ''),
                name=data.get('name', request.user.username),
                roll=data.get('roll', None)
            )
            
            # Handle GPS location if provided
            gps = data.get('gpsLocation')
            if gps:
                complaint.latitude = gps.get('latitude')
                complaint.longitude = gps.get('longitude')
                complaint.gps_accuracy = gps.get('accuracy')
                complaint.save()
            
            # Handle files if any
            files = data.get('files', [])
            for file_data in files:
                if file_data.get('data'):
                    try:
                        from django.core.files.base import ContentFile
                        
                        # Handle different base64 formats
                        if ';base64,' in file_data['data']:
                            format, imgstr = file_data['data'].split(';base64,')
                        else:
                            imgstr = file_data['data']
                        
                        file_content = ContentFile(base64.b64decode(imgstr), name=file_data['name'])
                        
                        ComplaintFile.objects.create(
                            complaint=complaint,
                            file=file_content,
                            name=file_data['name']
                        )
                    except Exception as e:
                        print(f"Error saving file {file_data.get('name')}: {str(e)}")
            
            # Create notification for user
            Notification.objects.create(
                user=request.user,
                title='Complaint Filed',
                message=f'Your complaint {complaint.complaint_id} has been submitted successfully.',
                type='success',
                complaint=complaint
            )
            
            # Create notification for admins
            admin_users = User.objects.filter(is_superuser=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title='New Complaint',
                    message=f'New complaint {complaint.complaint_id} filed by {request.user.username}',
                    type='info',
                    complaint=complaint
                )
            
            return JsonResponse({
                'success': True,
                'complaint_id': complaint.complaint_id,
                'message': 'Complaint submitted successfully!'
            })
            
        except Exception as e:
            print(f"Submit complaint error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_complaints(request):
    """API endpoint to get complaints"""
    try:
        user = request.user
        is_admin = user.is_superuser
        
        if is_admin:
            complaints = Complaint.objects.all().order_by('-submitted_at')
        else:
            complaints = Complaint.objects.filter(user=user).order_by('-submitted_at')
        
        data = []
        for c in complaints:
            files = [{
                'id': f.id,
                'name': f.name,
                'url': f.file.url if f.file else None,
                'type': f.file.name.split('.')[-1] if f.file else 'unknown',
                'size': f.file.size if f.file else 0
            } for f in c.files.all()]
            
            data.append({
                'id': c.complaint_id,
                'complaint_type': c.complaint_type,
                'urgency': c.urgency,
                'location': c.location,
                'latitude': c.latitude,
                'longitude': c.longitude,
                'details': c.details,
                'name': c.name,
                'roll': c.roll,
                'status': c.status,
                'submitted_at': c.submitted_at.isoformat(),
                'updated_at': c.updated_at.isoformat(),
                'files': files,
                'has_gps': bool(c.latitude and c.longitude),
                'rating': c.rating,
                'feedback': c.feedback,
                'feedback_submitted_at': c.feedback_submitted_at.isoformat() if c.feedback_submitted_at else None,
                'reopened': c.reopened,
                'reopen_reason': c.reopen_reason,
                'reopen_count': c.reopen_count,
                'user_name': c.user.username,
                'user_email': c.user.email
            })
        
        return JsonResponse({'success': True, 'complaints': data})
    except Exception as e:
        print(f"Get complaints error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@login_required
def update_status(request):
    """API endpoint to update complaint status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            complaint_id = data.get('complaint_id')
            new_status = data.get('status')
            
            complaint = Complaint.objects.get(complaint_id=complaint_id)
            
            # Check permission (admin or own complaint)
            if not request.user.is_superuser and complaint.user != request.user:
                return JsonResponse({'success': False, 'message': 'Permission denied'})
            
            old_status = complaint.status
            complaint.status = new_status
            complaint.save()
            
            # Notify user
            Notification.objects.create(
                user=complaint.user,
                title='Status Updated',
                message=f'Your complaint {complaint.complaint_id} status changed from {old_status} to {new_status}',
                type='info',
                complaint=complaint
            )
            
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
            
        except Complaint.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Complaint not found'})
        except Exception as e:
            print(f"Update status error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def delete_complaint(request):
    """API endpoint to delete a complaint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            complaint_id = data.get('complaint_id')
            
            complaint = Complaint.objects.get(complaint_id=complaint_id)
            
            # Check permission (admin only)
            if not request.user.is_superuser:
                return JsonResponse({'success': False, 'message': 'Permission denied'})
            
            complaint.delete()
            
            return JsonResponse({'success': True, 'message': 'Complaint deleted successfully'})
            
        except Complaint.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Complaint not found'})
        except Exception as e:
            print(f"Delete complaint error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def submit_feedback(request):
    """API endpoint to submit feedback"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            complaint_id = data.get('complaint_id')
            rating = data.get('rating')
            feedback = data.get('feedback')
            
            complaint = Complaint.objects.get(complaint_id=complaint_id, user=request.user)
            
            complaint.rating = rating
            complaint.feedback = feedback
            complaint.feedback_submitted_at = timezone.now()
            complaint.save()
            
            # Notify admins
            admin_users = User.objects.filter(is_superuser=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title='New Feedback',
                    message=f'Complaint {complaint.complaint_id} received {rating}/5 rating',
                    type='info',
                    complaint=complaint
                )
            
            return JsonResponse({'success': True, 'message': 'Feedback submitted successfully'})
            
        except Complaint.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Complaint not found'})
        except Exception as e:
            print(f"Submit feedback error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def reopen_complaint(request):
    """API endpoint to reopen a complaint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            complaint_id = data.get('complaint_id')
            reason = data.get('reason')
            
            complaint = Complaint.objects.get(complaint_id=complaint_id, user=request.user)
            
            complaint.status = 'reopened'
            complaint.reopened = True
            complaint.reopen_reason = reason
            complaint.reopen_count += 1
            complaint.save()
            
            # Notify admins
            admin_users = User.objects.filter(is_superuser=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title='Complaint Reopened',
                    message=f'Complaint {complaint.complaint_id} reopened by {request.user.username}. Reason: {reason}',
                    type='warning',
                    complaint=complaint
                )
            
            return JsonResponse({'success': True, 'message': 'Complaint reopened successfully'})
            
        except Complaint.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Complaint not found'})
        except Exception as e:
            print(f"Reopen complaint error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_notifications(request):
    """API endpoint to get user notifications"""
    try:
        notifications = Notification.objects.filter(
            user=request.user,
            read=False
        ).order_by('-created_at')[:20]
        
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'complaint_id': n.complaint.complaint_id if n.complaint else None,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
        
        return JsonResponse({'success': True, 'notifications': data})
    except Exception as e:
        print(f"Get notifications error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@login_required
def mark_notification_read(request):
    """API endpoint to mark notification as read"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')
            
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.read = True
            notification.read_at = timezone.now()
            notification.save()
            
            return JsonResponse({'success': True})
            
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Notification not found'})
        except Exception as e:
            print(f"Mark notification read error: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def get_dashboard_stats(request):
    """API endpoint to get dashboard statistics - FIXED"""
    try:
        user = request.user
        is_admin = user.is_superuser
        
        if is_admin:
            complaints = Complaint.objects.all()
            total_users = User.objects.count()
        else:
            complaints = Complaint.objects.filter(user=user)
            total_users = None
        
        total = complaints.count()
        pending = complaints.filter(status='pending').count()
        progress = complaints.filter(status='progress').count()
        resolved = complaints.filter(status='resolved').count()
        reopened = complaints.filter(status='reopened').count()
        high_urgency = complaints.filter(urgency='High').count()
        
        # Category breakdown
        categories = {}
        for c in complaints:
            cat = c.complaint_type
            categories[cat] = categories.get(cat, 0) + 1
        
        # Average rating
        rated = complaints.exclude(rating__isnull=True)
        avg_result = rated.aggregate(Avg('rating'))
        avg_rating = avg_result['rating__avg'] or 0
        
        stats = {
            'total': total,
            'pending': pending,
            'progress': progress,
            'resolved': resolved,
            'reopened': reopened,
            'high_urgency': high_urgency,
            'categories': categories,
            'avg_rating': round(avg_rating, 1),
            'total_users': total_users,
        }
        
        return JsonResponse({'success': True, 'stats': stats})
    except Exception as e:
        print(f"Error in get_dashboard_stats: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def get_admin_data(request):
    """API endpoint to get admin panel data"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        complaints = Complaint.objects.all().order_by('-submitted_at')
        users = User.objects.all()
        
        # Calculate overdue complaints (>3 days pending)
        now = timezone.now()
        overdue = complaints.filter(
            status__in=['pending', 'progress'],
            submitted_at__lte=now - timedelta(days=3)
        ).count()
        
        with_files = complaints.exclude(files__isnull=True).count()
        
        data = [{
            'id': c.complaint_id,
            'user_name': c.user.username,
            'user_email': c.user.email,
            'complaint_type': c.complaint_type,
            'urgency': c.urgency,
            'location': c.location,
            'details': c.details[:100] + ('...' if len(c.details) > 100 else ''),
            'full_details': c.details,
            'status': c.status,
            'submitted_at': c.submitted_at.isoformat(),
            'submitted_date': c.submitted_at.strftime('%Y-%m-%d'),
            'submitted_time': c.submitted_at.strftime('%H:%M'),
            'has_files': c.files.exists(),
            'files_count': c.files.count(),
            'rating': c.rating,
            'days_pending': (now - c.submitted_at).days if c.status in ['pending', 'progress'] else 0,
        } for c in complaints]
        
        return JsonResponse({
            'success': True,
            'complaints': data,
            'stats': {
                'total_complaints': complaints.count(),
                'total_users': users.count(),
                'with_files': with_files,
                'pending_overdue': overdue,
            }
        })
    except Exception as e:
        print(f"Get admin data error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def check_reminders(request):
    """API endpoint to check and send reminders"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        now = timezone.now()
        reminder_days = 3
        
        pending_complaints = Complaint.objects.filter(
            status__in=['pending', 'progress'],
            reminder_sent=False,
            submitted_at__lte=now - timedelta(days=reminder_days)
        )
        
        reminders_sent = 0
        for complaint in pending_complaints:
            days_pending = (now - complaint.submitted_at).days
            
            # Notify user
            Notification.objects.create(
                user=complaint.user,
                title='Pending Complaint Reminder',
                message=f'Your complaint {complaint.complaint_id} is pending for {days_pending} days.',
                type='warning',
                complaint=complaint
            )
            
            # Notify admins
            admin_users = User.objects.filter(is_superuser=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title='⚠️ Pending Complaint',
                    message=f'Complaint {complaint.complaint_id} pending for {days_pending} days',
                    type='warning',
                    complaint=complaint
                )
            
            complaint.reminder_sent = True
            complaint.reminder_sent_at = now
            complaint.save()
            reminders_sent += 1
        
        return JsonResponse({
            'success': True,
            'reminders_sent': reminders_sent,
            'message': f'Sent {reminders_sent} reminders'
        })
    except Exception as e:
        print(f"Check reminders error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

def get_user_session(request):
    """Check if user is logged in"""
    if request.user.is_authenticated:
        return JsonResponse({
            'is_authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'is_superuser': request.user.is_superuser,
                'is_admin': request.user.is_superuser  # For compatibility
            }
        })
    return JsonResponse({'is_authenticated': False})

@csrf_exempt
def api_logout(request):
    """API endpoint for logout"""
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True, 'message': 'Logged out successfully'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})