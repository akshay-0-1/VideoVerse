import os
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, Token, VideoSummary
from .serializers import UserSerializer, TokenSerializer
from django.conf import settings
from datetime import datetime, timedelta
import hashlib
import uuid
from django.utils import timezone
from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
import jwt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from urllib.parse import unquote
import yt_dlp
import assemblyai as aai
from cloudinary.uploader import upload
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate

SALT = "8b4f6b2cc1868d75ef79e5cfb8779c11b6a374bf0fce05b485581bf4e1e25b96c8c2855015de8449"
URL = "http://localhost:5173"


def mail_template(content, button_url, button_text):
    return f"""<!DOCTYPE html>
            <html>
            <body style="text-align: center; font-family: "Verdana", serif; color: #000;">
                <div style="max-width: 600px; margin: 10px; background-color: #fafafa; padding: 25px; border-radius: 20px;">
                <p style="text-align: left;">{content}</p>
                <a href="{button_url}" target="_blank">
                    <button style="background-color: #444394; border: 0; width: 200px; height: 30px; border-radius: 6px; color: #fff;">{button_text}</button>
                </a>
                <p style="text-align: left;">
                    If you are unable to click the above button, copy paste the below URL into your address bar
                </p>
                <a href="{button_url}" target="_blank">
                    <p style="margin: 0px; text-align: left; font-size: 10px; text-decoration: none;">{button_url}</p>
                </a>
                </div>
            </body>
            </html>"""


# Create your views here.
class ResetPasswordView(APIView):
    def post(self, request, format=None):
        user_id = request.data["id"]
        token = request.data["token"]
        password = request.data["password"]

        token_obj = Token.objects.filter(
            user_id=user_id).order_by("-created_at")[0]
        if token_obj.expires_at < timezone.now():
            return Response(
                {
                    "success": False,
                    "message": "Password Reset Link has expired!",
                },
                status=status.HTTP_200_OK,
            )
        elif token_obj is None or token != token_obj.token or token_obj.is_used:
            return Response(
                {
                    "success": False,
                    "message": "Reset Password link is invalid!",
                },
                status=status.HTTP_200_OK,
            )
        else:
            token_obj.is_used = True
            hashed_password = make_password(password=password, salt=SALT)
            ret_code = User.objects.filter(
                id=user_id).update(password=hashed_password)
            if ret_code:
                token_obj.save()
                return Response(
                    {
                        "success": True,
                        "message": "Your password reset was successfully!",
                    },
                    status=status.HTTP_200_OK,
                )


class ForgotPasswordView(APIView):
    def post(self, request, format=None):
        email = request.data["email"]
        user = User.objects.get(email=email)
        created_at = timezone.now()
        expires_at = timezone.now() + timezone.timedelta(1)
        salt = uuid.uuid4().hex
        token = hashlib.sha512(
            (str(user.id) + user.password + created_at.isoformat() + salt).encode(
                "utf-8"
            )
        ).hexdigest()
        token_obj = {
            "token": token,
            "created_at": created_at,
            "expires_at": expires_at,
            "user_id": user.id,
        }
        serializer = TokenSerializer(data=token_obj)
        if serializer.is_valid():
            serializer.save()
            subject = "Forgot Password Link"
            content = mail_template(
                "We have received a request to reset your password. Please reset your password using the link below.",
                f"{URL}/resetPassword?id={user.id}&token={token}",
                "Reset Password",
            )
            send_mail(
                subject=subject,
                message=content,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                html_message=content,
            )
            return Response(
                {
                    "success": True,
                    "message": "A password reset link has been sent to your email.",
                },
                status=status.HTTP_200_OK,
            )
        else:
            error_msg = ""
            for key in serializer.errors:
                error_msg += serializer.errors[key][0]
            return Response(
                {
                    "success": False,
                    "message": error_msg,
                },
                status=status.HTTP_200_OK,
            )


class RegistrationView(APIView):
    def post(self, request, format=None):
        request.data["password"] = make_password(
            password=request.data["password"], salt=SALT
        )
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "You are now registered on our website!"},
                status=status.HTTP_201_CREATED,  # Use 201 Created status
            )
        else:
            error_msg = ""
            for key in serializer.errors:
                error_msg += f"{key}: {serializer.errors[key][0]} "
            print(f"Registration error: {error_msg}")  # Log the error message
            return Response(
                {"success": False, "message": error_msg},
                status=status.HTTP_400_BAD_REQUEST,  # Use 400 Bad Request status
            )


class LoginView(APIView):
    def post(self, request, format=None):
        email = request.data["email"]
        password = request.data["password"]
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "Invalid Login Credentials!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if check_password(password, user.password):
            # Generate JWT token
            token = jwt.encode(
                {'user_id': user.id, 'email': user.email},
                settings.SECRET_KEY,
                algorithm='HS256'
            )
            
            # Set session data
            request.session['user_id'] = user.id
            request.session['email'] = user.email
            
            response = Response(
                {
                    "success": True,
                    "message": "You are now logged in!",
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "country": user.country,
                        "phone": user.phone
                    },
                    "token": token
                },
                status=status.HTTP_200_OK,
            )
            
            # Set cookie with JWT token
            response.set_cookie(
                'auth_token',
                token,
                httponly=True,
                secure=True,  # Use True in production with HTTPS
                samesite='Lax',
                max_age=86400  # 24 hours
            )
            
            return response
        else:
            return Response(
                {"success": False, "message": "Invalid Login Credentials!"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutView(APIView):
    def post(self, request, format=None):
        # Clear the session
        request.session.flush()
        
        response = Response(
            {"success": True, "message": "Successfully logged out!"},
            status=status.HTTP_200_OK,
        )
        
        # Clear the auth cookie
        response.delete_cookie('auth_token')
        
        return response


@csrf_exempt
@login_required
def video_summaries(request):
    summaries = VideoSummary.objects.filter(user=request.user).order_by('-created_at')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'summaries': list(summaries.values())
        })
    return render(request, 'all-summaries.html', {'video_summaries': summaries})


@csrf_exempt
@login_required
def summary_details(request, pk):
    summary = get_object_or_404(VideoSummary, pk=pk, user=request.user)
    return JsonResponse({
        'success': True,
        'summary': {
            'id': summary.id,
            'youtube_title': summary.youtube_title,
            'youtube_link': summary.youtube_link,
            'summary_content': summary.summary_content,
            'created_at': summary.created_at
        }
    })


@csrf_exempt
def generate_summary(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = unquote(data['link'])
            
            # Validate that link is provided
            if not yt_link:
                return JsonResponse({'error': 'YouTube URL is required'}, status=400)
            
            print(f"Processing YouTube link: {yt_link}")
            request.session['progress_message'] = "Processing YouTube link..."
            
            # Enhanced YouTube URL validation
            if not any(domain in yt_link.lower() for domain in ['youtube.com', 'youtu.be']):
                return JsonResponse({'error': 'Invalid YouTube URL format'}, status=400)
            
            try:
                # Get video title with timeout handling
                request.session['progress_message'] = "Fetching video title..."
                title = yt_title(yt_link)
                
                if not title:
                    return JsonResponse({'error': 'Could not access video. Please check if the video is public.'}, status=400)
                
                # Process audio and get summary
                request.session['progress_message'] = "Converting video to audio..."
                result = get_transcription(yt_link)
                
                if not result.get('transcription'):
                    return JsonResponse({'error': "Failed to transcribe video"}, status=500)
                
                if not result.get('summary'):
                    return JsonResponse({'error': "Failed to generate summary"}, status=500)

                # Save the summary
                request.session['progress_message'] = "Saving summary..."
                new_summary = VideoSummary.objects.create(
                    user=request.user,
                    youtube_title=title,
                    youtube_link=yt_link,
                    summary_content=result['summary']
                )
                
                return JsonResponse({
                    'success': True,
                    'summary': {
                        'id': new_summary.id,
                        'title': title,
                        'content': result['summary'],
                        'youtube_link': yt_link
                    }
                })
                
            except Exception as e:
                print(f"Processing error: {str(e)}")
                return JsonResponse({
                    'error': 'Failed to process video',
                    'details': str(e)
                }, status=500)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except KeyError:
            return JsonResponse({'error': 'Missing YouTube URL in request'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

def get_transcription(link):
    """Get transcription from audio file using AssemblyAI."""
    try:
        print("Starting download_audio...")
        audio_url = download_audio(link)  # This now returns a Cloudinary URL
        print(f"Audio file uploaded successfully: {audio_url}")
        
        print("Setting up AssemblyAI...")
        aai.settings.api_key = "394cdb03355a4f3e89b331815f9337e6"
        
        print("Creating transcriber...")
        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(
            summarization=True,
            summary_model=aai.SummarizationModel.informative,
            summary_type=aai.SummarizationType.paragraph
        )
        
        print("Starting transcription...")
        transcript = transcriber.transcribe(audio_url, config=config)  # AssemblyAI can handle URLs directly
        print("Transcription completed successfully")
        
        if not transcript.text or not transcript.summary:
            raise Exception("Transcription or summary is empty")
        
        return {
            'transcription': transcript.text,
            'summary': transcript.summary
        }
    except Exception as e:
        import traceback
        print(f"Transcription error: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        raise

def download_audio(link):
    """Download audio from YouTube video link."""
    try:
        temp_dir = '/tmp' if not settings.DEBUG else settings.MEDIA_ROOT
        os.makedirs(temp_dir, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'no_color': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Starting download...")
            info = ydl.extract_info(link, download=True)
            temp_file_path = os.path.join(temp_dir, f"{info['id']}.mp3")
            
            if not os.path.exists(temp_file_path):
                raise Exception(f"Audio file not found at {temp_file_path}")
            
            # Upload to Cloudinary
            from cloudinary.uploader import upload
            result = upload(temp_file_path, 
                          resource_type="auto",
                          folder="youtube_audio")
            
            # Clean up the temporary file
            os.remove(temp_file_path)
            
            # Return the Cloudinary URL
            return result['url']
            
    except Exception as e:
        print(f"Error in download_audio: {str(e)}")
        raise

def yt_title(link):
    """Fetch the YouTube video title."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'no_color': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(link, download=False)
            return info.get('title')
        except Exception as e:
            print(f"Error in yt_title: {str(e)}")
            raise

@api_view(['GET'])
def verify_token(request):
    token = request.headers.get('Authorization', '').split(' ')[1]
    
    if not token:
        return Response({'error': 'No token provided'}, status=status.HTTP_401_UNAUTHORIZED)
        
    try:
        # Verify the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        # Check if user exists
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise jwt.InvalidTokenError
            
        return Response({'valid': True}, status=status.HTTP_200_OK)
        
    except jwt.ExpiredSignatureError:
        return Response({'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'message': 'Please provide both email and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    user = authenticate(username=email, password=password)
    
    if user is not None:
        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
        }, settings.SECRET_KEY, algorithm='HS256')
        
        return Response({
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'message': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)