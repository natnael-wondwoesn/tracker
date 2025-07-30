from django.conf import settings
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle
from .serializers import UserListSerializer, UserRegistrationSerializer, ChildProfileSerializer, LoginSerializer
from .models import PendingUser, CustomUser, ChildProfile, Parent, Therapist  
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.core.mail import send_mail
from smtplib import SMTPAuthenticationError
from django.contrib.auth.hashers import make_password
import os 
import uuid
from django.contrib.auth.hashers import check_password
import logging
from django.contrib.auth import get_user_model

CustomUser = get_user_model()
logger = logging.getLogger(__name__)

class UserMeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve the authenticated user's details."""
        try:
            user = request.user
            serializer = UserListSerializer(user)
            logger.info(f"User {user.email} retrieved their own details")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving user details for {request.user.email}: {str(e)}")
            return Response(
                {"error": "Failed to retrieve user details"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Retrieve a single user by ID for admin users."""
        try:
            user = CustomUser.objects.get(id=user_id)
            serializer = UserListSerializer(user)
            logger.info(f"Admin {request.user.email} retrieved user {user.email} (ID: {user_id})")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            logger.warning(f"User {user_id} not found for admin {request.user.email}")
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}")
            return Response(
                {"error": "Failed to retrieve user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            users = CustomUser.objects.all()
            serializer = UserListSerializer(users, many=True)
            logger.info(f"Admin {request.user.email} retrieved list of {len(users)} users")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving user list: {str(e)}")
            return Response(
                {"error": "Failed to retrieve user list"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
# class RegisterUserView(APIView):
    # permission_classes = [AllowAny]

    # def post(self, request):
    #     serializer = UserRegistrationSerializer(data=request.data)
    #     if serializer.is_valid():
    #         validated_data = serializer.validated_data
    #         email = validated_data['email']
    #         phone_number = validated_data['phone_number']
    #         first_name = validated_data['first_name']
    #         last_name = validated_data['last_name']
    #         role = validated_data['role']
    #         password = validated_data['password']
    #         edu_document = validated_data.get('edu_document')

    #         # Validate edu_document only for therapists
    #         if role == 'therapist' and not edu_document:
    #             logger.warning(f"Therapist registration attempt for {email} without edu_document")
    #             return Response(
    #                 {'error': 'Educational document is required for therapist registration.'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         # Check if user already exists in CustomUser
    #         if CustomUser.objects.filter(email=email).exists():
    #             return Response(
    #                 {'error': 'A user with this email already exists.'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         try:
    #             # Create user in CustomUser
    #             user = CustomUser.objects.create_user(
    #                 email=email,
    #                 phone_number=phone_number,
    #                 first_name=first_name,
    #                 last_name=last_name,
    #                 role=role,
    #                 password=password  # create_user will hash the password
    #             )

    #             # For therapists, create a Therapist record
    #             if role == 'therapist':
    #                 Therapist.objects.create(
    #                     user=user,
    #                     edu_document=edu_document,
    #                     admin_approved=False  # Default to not approved
    #                 )
    #                 logger.info(f"Therapist record created for {email} in core_therapist")

    #             logger.info(f'User {email} registered successfully with role {role}')
    #             return Response(
    #                 {'message': 'User registered successfully.'},
    #                 status=status.HTTP_201_CREATED
    #             )
    #         except Exception as e:
    #             logger.error(f'Error registering user {email}: {str(e)}')
    #             return Response(
    #                 {'error': f'Failed to register user: {str(e)}'},
    #                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
    #             )

    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)# class RegisterUserView(APIView):
class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
       
        serializer = UserRegistrationSerializer(data=request.data)  
        if serializer.is_valid():
            validated_data = serializer.validated_data
            email = validated_data['email']
            phone_number = validated_data['phone_number']
            first_name = validated_data['first_name']
            last_name = validated_data['last_name']
            role = validated_data['role']
            password = validated_data['password']  # Don't hash here, create_user will do it
            edu_document = validated_data.get('edu_document')

            # Validate edu_document for therapists
            if role == 'therapist' and not edu_document:
                logger.warning(f"Therapist registration attempt for {email} without edu_document")
                return Response(
                    {'error': 'Educational document is required for therapist registration.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Check if user already exists in CustomUser
            if CustomUser.objects.filter(email=email).exists():
                return Response(
                    {'error': 'A user with this email already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            pending_user = PendingUser.objects.filter(email=email).first()
            if pending_user:
                # Delete stale records older than 1 hour
                if pending_user.created_at < timezone.now() - timedelta(hours=1):
                    if pending_user.edu_document:
                        try:
                            os.remove(pending_user.edu_document.path)
                        except FileNotFoundError:
                            pass
                    pending_user.delete()
                else:
                    return Response(
                        {'error': 'A verification email has already been sent for this email. Please check your inbox or try again later.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            try:
                # Create pending user
                verification_token = str(uuid.uuid4())
                pending_user = PendingUser(
                    email=email,
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    password=password,  # Store raw password, will be hashed when creating actual user
                    verification_token=verification_token,
                    edu_document=edu_document
                )
                pending_user.save()

                # Send verification email
                verification_link = f"{settings.APP_URL}/core/verify-email/?token={verification_token}"
                try:
                    send_mail(
                        subject='Verify Your Email',
                        message=f'Click the link to verify your email: {verification_link}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=f'<p>Click <a href="{verification_link}">here</a> to verify your email.</p>',
                        fail_silently=False,  # Raise exceptions for debugging
                    )
                    logger.info(f'Verification email sent to {email}')
                    return Response(
                        {'message': 'Verification email sent. Please check your inbox.'},
                        status=status.HTTP_200_OK
                    )
                except SMTPAuthenticationError as e:
                    logger.error(f'SMTP Authentication Error for {email}: {str(e)}')
                    if pending_user.edu_document:
                        try:
                            os.remove(pending_user.edu_document.path)
                        except FileNotFoundError:
                            pass
                    pending_user.delete()
                return Response(
                    {'error': 'Failed to send verification email due to authentication issues.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as e:
                logger.error(f'Error sending email to {email}: {str(e)}')
                if pending_user.edu_document:
                    try:
                        os.remove(pending_user.edu_document.path)
                    except FileNotFoundError:
                        pass
                pending_user.delete()
                return Response(
                    {'error': f'Failed to send verification email: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.GET.get('token')
        if not token:
            return Response(
                {'error': 'Verification token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            pending_user = PendingUser.objects.get(verification_token=token)
            if pending_user.is_verified:
                if pending_user.role == 'parent':
                    if CustomUser.objects.filter(email=pending_user.email).exists():
                        logger.info(f"Parent user {pending_user.email} already verified and activated")
                        return Response({"message": "Email already verified. Parent account activated."}, status=status.HTTP_200_OK)
                elif pending_user.role == 'therapist':
                    logger.info(f"Therapist user {pending_user.email} already verified, pending admin approval")
                    return Response({"message": "Email already verified. Therapist account awaiting admin approval."}, status=status.HTTP_200_OK)
                        
            if pending_user.role == 'parent':
                # Check if CustomUser already exists
                if CustomUser.objects.filter(email=pending_user.email).exists():
                    logger.warning(f"Parent user {pending_user.email} already exists in CustomUser")
                    return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
                
                # Create CustomUser
                user = CustomUser.objects.create_user(
                    email=pending_user.email,
                    first_name=pending_user.first_name,
                    last_name=pending_user.last_name,
                    phone_number=pending_user.phone_number,
                    password=pending_user.password,  # Raw password, create_user will hash it
                    role=pending_user.role
                )
                
                user.is_active = True
                user.save()
                if not Parent.objects.filter(user=user).exists():
                    Parent.objects.create(user=user)
                logger.info(f"Parent user {user.email} verified and activated successfully")
                pending_user.delete()  # Delete PendingUser for parents
                return Response(
                    {"message": "Email verified successfully. Parent account activated."},
                    status=status.HTTP_200_OK
                )

            elif pending_user.role == 'therapist':
                pending_user.is_verified = True
                pending_user.save()
                logger.info(f"Therapist user {pending_user.email} verified, pending admin approval")
                return Response(
                    {"message": "Email verified successfully. Therapist account awaiting admin approval."},
                    status=status.HTTP_200_OK
                )
            else:
                logger.warning(f"Invalid role {pending_user.role} for user {pending_user.email}")
                pending_user.delete()
                return Response(
                    {"error": "Invalid user role"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except PendingUser.DoesNotExist:
            return Response({"error": "Invalid verification token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            return Response({"error": "An error occurred while verifying your email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AdminLoginView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            logger.warning("Missing email or password in admin login request")
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(email=email, password=password)
        if user is None:
            logger.warning(f"Invalid credentials for admin login: {email}")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            logger.warning(f"Inactive admin account attempted login: {email}")
            return Response(
                {'error': 'Account is not active.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.role != 'admin':
            logger.warning(f"Non-admin user attempted admin login: {email}, role: {user.role}")
            return Response(
                {'error': 'Only users with admin role can log in.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            refresh = RefreshToken.for_user(user)
            logger.info(f"Admin login successful for {email}")
            return Response({
                'message': 'Login successful.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error generating JWT for {email}: {str(e)}")
            return Response(
                {'error': 'Failed to generate token.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
                
class AdminApprovalView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        email = request.data.get('email')
        action = request.data.get('action')

        if not email:
            logger.warning("No email provided in admin approval request")
            return Response({"error": "email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not action or action not in ['approve', 'reject']:
            logger.warning(f"Invalid or missing action in admin approval request: {action}")
            return Response({"error": "action must be 'approve' or 'reject'"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pending_user = PendingUser.objects.get(email=email, role='therapist', is_verified=True)
            
            if action == 'reject':
                logger.info(f"Therapist {email} rejected by admin")
                pending_user.delete()
                return Response({"message": f"Therapist {email} rejected successfully"}, status=status.HTTP_200_OK)

            # Action is 'approve'
            # Check if CustomUser already exists
            if CustomUser.objects.filter(email=email).exists():
                logger.warning(f"Therapist user {email} already exists in CustomUser")
                pending_user.delete()
                return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Create CustomUser
            user = CustomUser.objects.create_user(
                email=pending_user.email,
                first_name=pending_user.first_name,
                last_name=pending_user.last_name,
                phone_number=pending_user.phone_number,
                password=pending_user.password,  # Raw password, create_user will hash it
                role=pending_user.role
            )
            user.is_active = True  # Activate upon approval
            user.save()

            # Create Therapist with edu_document
            if not Therapist.objects.filter(user=user).exists():
                Therapist.objects.create(
                    user=user,
                    edu_document=pending_user.edu_document
                )

            logger.info(f"Therapist {email} approved and activated by admin")
            pending_user.delete()  # Delete PendingUser after approval
            return Response({"message": f"Therapist {email} approved successfully"}, status=status.HTTP_200_OK)

        except PendingUser.DoesNotExist:
            logger.warning(f"Pending user not found for email: {email}")
            return Response({"error": "Pending user not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error processing therapist {email} with action {action}: {str(e)}")
            return Response({"error": f"An error occurred while processing the request: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            logger.warning("Missing email or password in login request")
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # First try to get the user
            user = CustomUser.objects.get(email=email)
            
            # Then check if the password is correct
            if not user.check_password(password):
                logger.warning(f"Invalid password for user: {email}")
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive account attempted login: {email}")
                return Response(
                    {'error': 'Account is not active.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            logger.info(f"Login successful for {email}")
            return Response({
                'message': 'Login successful.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'email': user.email,
                    'role': user.role,
                    'id': user.id
                }
            }, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            logger.warning(f"User not found: {email}")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Error during login for {email}: {str(e)}")
            return Response(
                {'error': 'Failed to process login request.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"message": "Successfully logged out"}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return Response(
                {"error": "Failed to logout"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChildProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all child profiles for the authenticated parent."""
        if request.user.role != 'parent':
            logger.warning(f"Non-parent user {request.user.email} attempted to access child profiles")
            return Response({"error": "Only parents can access child profiles"}, status=status.HTTP_403_FORBIDDEN)
        profiles = ChildProfile.objects.filter(parent=request.user)
        serializer = ChildProfileSerializer(profiles, many=True, context={'request': request})
        logger.info(f"Retrieved {len(serializer.data)} child profiles for {request.user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        if request.user.role != 'parent':
            logger.warning(f"Non-parent user {request.user.email} attempted to create child profile")
            return Response({"error": "Only parents can create child profiles"}, status=status.HTTP_403_FORBIDDEN)
        
        # Ensure a Parent record exists for the user
        parent, created = Parent.objects.get_or_create(user=request.user)
        if created:
            logger.info(f"Created new Parent record for user {request.user.email}")

        serializer = ChildProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Save the child profile with the parent (CustomUser)
                child_profile = serializer.save(parent=request.user)
                
                # Set active_child if this is the first child
                if not parent.active_child:
                    parent.active_child = child_profile
                    parent.save()
                    logger.info(f"Set first child {child_profile.full_name} as active for parent {request.user.email}")
                
                logger.info(f"Child profile created successfully for {request.user.email}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Rollback child creation if something fails
                child_profile.delete()
                logger.error(f"Error setting up child profile: {str(e)}")
                return Response({"error": "Failed to create child profile"}, status=status.HTTP_400_BAD_REQUEST)
        logger.error(f"Error creating child profile for {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, child_id):
        if request.user.role != 'parent':
            logger.warning(f"Non-parent user {request.user.email} attempted to update child profile {child_id}")
            return Response({"error": "Only parents can update child profiles"}, status=status.HTTP_403_FORBIDDEN)
        try:
            profile = ChildProfile.objects.get(id=child_id, parent=request.user)
        except ChildProfile.DoesNotExist:
            logger.warning(f"Child profile {child_id} not found for parent {request.user.email}")
            return Response({"error": "Child profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ChildProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Child profile {child_id} updated successfully for parent {request.user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.error(f"Error updating child profile {child_id} for parent {request.user.email}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, child_id):
        if request.user.role != 'parent':
            logger.warning(f"Non-parent user {request.user.email} attempted to delete child profile {child_id}")
            return Response({"error": "Only parents can delete child profiles"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            profile = ChildProfile.objects.get(id=child_id, parent=request.user)
            profile.delete()
            logger.info(f"Child profile {child_id} deleted successfully for parent {request.user.email}")
            return Response({"message": "Child profile deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except ChildProfile.DoesNotExist:
            logger.warning(f"Child profile {child_id} not found for parent {request.user.email}")
            return Response({"error": "Child profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
class SwitchActiveChildView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, child_id):
        """Switch the active child for the parent."""
        if request.user.role != 'parent':
            logger.warning(f"Non-parent user {request.user.email} attempted to switch active child")
            return Response(
                {"error": "Only parents can switch active children"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Verify the child belongs to the parent
            child_profile = ChildProfile.objects.get(id=child_id, parent=request.user)
            
            # Update the parent's active child
            parent = Parent.objects.get(user=request.user)
            parent.active_child = child_profile
            parent.save()
            
            logger.info(f"Switched active child to {child_profile.full_name} for parent {request.user.email}")
            return Response({
                "message": f"Successfully switched to {child_profile.full_name}",
                "active_child": ChildProfileSerializer(child_profile).data
            }, status=status.HTTP_200_OK)
            
        except ChildProfile.DoesNotExist:
            logger.warning(f"Child profile {child_id} not found for parent {request.user.email}")
            return Response(
                {"error": "Child profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error switching active child for {request.user.email}: {str(e)}")
            return Response(
                {"error": "Failed to switch active child"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



