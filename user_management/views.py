from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta, datetime, timezone as dt_timezone
from django.utils import timezone
from .models import xx_User, xx_UserLevel,xx_notification
from .serializers import ChangePasswordSerializer, NotificationSerializer, RegisterSerializer, LoginSerializer, UserLevelSerializer
from .permissions import IsAdmin
from .utils import send_notification
# from test_querty import LLMQueryGenerator
# from django.db import connection
# Authentication Views
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    """Register a new user"""
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'data': RegisterSerializer(user).data,
                'message': 'User registered successfully.',
                'token': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class LoginView(APIView):
    """Authenticate a user and return a token"""
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'data': RegisterSerializer(user).data,
                'message': 'Login successful.',
                'token': str(refresh.access_token),
            })
            
        return Response({'message': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
class TokenExpiredView(APIView):
    """Check if the token is expired"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token_created_at = request.auth.payload.get('iat', None)
        if token_created_at:
            expiration_minutes = 1440  # 24 hours
            created_time = datetime.fromtimestamp(token_created_at, tz=dt_timezone.utc)
            if timezone.now() > created_time + timedelta(minutes=expiration_minutes):
                return Response({
                    'data': [],
                    'message': 'Token expired.',
                    'token': None
                }, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'data': RegisterSerializer(request.user).data,
            'message': 'Token valid.',
            'token': str(request.auth)
        })


# User Management Views
class ListUsersView(APIView):
    """List all users (admin only)"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        users = xx_User.objects.exclude(id=request.user.id)  # Exclude current admin
        data = []
        for user in users:
            data.append({
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'can_transfer_budget': user.can_transfer_budget,
                'user_level': user.user_level.name if user.user_level else 'None',
            })
        return Response(data)
class UpdateUserPermissionView(APIView):
    # """Update a user's permission to transfer budget (admin only)"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def put(self, request, user_id):
        try:
            user = xx_User.objects.get(id=user_id)
            can_transfer_budget = request.data.get('can_transfer_budget', False)
            
            # Update the permission
            user.can_transfer_budget = can_transfer_budget
            user.save()
            
            return Response({
                "message": f"Permissions updated for user {user.username}",
                "can_transfer_budget": user.can_transfer_budget
            })
        except xx_User.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
class UserUpdateView(APIView):
    """Update user data (e.g., username, role)."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return xx_User.objects.get(pk=pk)
        except xx_User.DoesNotExist:
            return None

    def put(self, request):
        pk = request.query_params.get('pk')
        user = self.get_object(pk)
        if user is None:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        for field in ['username', 'role', 'can_transfer_budget']:
            if field in request.data:
                setattr(user, field, request.data[field])

        user.save()
        return Response({
            'message': 'User updated successfully.',
            'data': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'can_transfer_budget': user.can_transfer_budget,
            }
        })
class UserDeleteView(APIView):
    """Delete a specific user."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return xx_User.objects.get(pk=pk)
        except xx_User.DoesNotExist:
            return None

    def delete(self, request):
        pk = request.query_params.get('pk')
        user = self.get_object(pk)
        if user is None:
            return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({'message': 'User deleted successfully.'}, status=status.HTTP_200_OK)


# User Level Views
class UpdateUserLevelView(APIView): # Update a user's level
    """Assign a specific user level to a user (admin only)"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def put(self, request):
        try:
            # Get the user

            # Get the level ID from request data
            level_id = request.data.get('level_order')
            user_id = request.data.get('user_id')

            user = xx_User.objects.get(id=user_id)


            if level_id is None:
                return Response({
                    'error': 'Missing level_id',
                    'message': 'Please provide a level_id to assign'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if the level exists
            try:
                user_level = xx_UserLevel.objects.get(level_order=level_id)
            except xx_UserLevel.DoesNotExist:
                return Response({
                    'error': 'Invalid level_id',
                    'message': f'No user level found with ID: {level_id}'
                }, status=status.HTTP_404_NOT_FOUND)

            # Update the user's level
            old_level = user.user_level.name if user.user_level else 'None'
            user.user_level = user_level
            user.save()

            return Response({
                'message': f'User level updated successfully for {user.username}',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'previous_level': old_level,
                    'new_level': user_level.name,
                    'level_order': user_level.level_order
                }
            }, status=status.HTTP_200_OK)

        except xx_User.DoesNotExist:
            return Response({
                'error': 'User not found',
                'message': f'No user found with ID: {user_id}'
            }, status=status.HTTP_404_NOT_FOUND)

class UserLevelCreateView(APIView):
    """Create a new user level"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request):
        serializer = UserLevelSerializer(data=request.data)
        if serializer.is_valid():
            # Check if level_order already exists
            level_order = serializer.validated_data.get('level_order')
            if xx_UserLevel.objects.filter(level_order=level_order).exists():
                return Response({
                    'error': 'Level order already exists',
                    'message': f'A user level with order {level_order} already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            serializer.save()
            return Response({
                'message': 'User level created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  

class UserLevelUpdateView(APIView): # Update the data of the Level itself
    """Update an existing user level (name, level_order)."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return xx_UserLevel.objects.get(pk=pk)
        except xx_UserLevel.DoesNotExist:
            return None

    def put(self, request):
        pk = request.query_params.get('pk')
        level = self.get_object(pk)
        if level is None:
            return Response({'message': 'User level not found.'}, status=status.HTTP_404_NOT_FOUND)

        for field in ["name", "level_order", "description"]:
            if field in request.data:
                setattr(level, field, request.data[field])

        level.save()
        return Response({
            'message': 'User level updated successfully.',
            'data': {
                'id': level.id,
                'name': level.name,
                'level_order': level.level_order,
                'description': level.description
            }
        })

class UserLevelDeleteView(APIView):
    """Delete a specific user level."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_object(self, pk):
        try:
            return xx_UserLevel.objects.get(pk=pk)
        except xx_UserLevel.DoesNotExist:
            return None

    def delete(self, request):
        pk = request.query_params.get('pk')
        level = self.get_object(pk)
        if level is None:
            return Response({'message': 'User level not found.'}, status=status.HTTP_404_NOT_FOUND)
        level.delete()
        return Response({'message': 'User level deleted successfully.'}, status=status.HTTP_200_OK)
class UserLevelListView(APIView):
    """List all user levels"""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get(self, request):
        levels = xx_UserLevel.objects.all()
        serializer = UserLevelSerializer(levels, many=True)
        return Response(serializer.data)


# Notification Views
class UnRead_Notification(APIView):
    """Create and list notifications for a user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        notifications = xx_notification.objects.filter(user=user, is_read=False, is_shown=True).order_by('created_at').reverse()
        count = notifications.count()
        data = [
            {
                'id': notification.id,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at,
                'is_shown': notification.is_shown,
                'is_system_read': notification.is_system_read
            } for notification in notifications
        ]
        return Response({
            'notifications': data,
            'count': count
        })
class System_Notification(APIView):
    """Create and list system notifications for all users"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        user = request.user
        notifications = xx_notification.objects.filter(user=user, is_system_read=False).order_by('created_at').reverse()
        count = notifications.count()
        for notification in notifications:
            notification.is_system_read = True
            notification.save()
        return Response({
            'Number_Of_Notifications': count,
        })
class Get_All_Notification(APIView):
    """Create and list system notifications for all users"""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        user = request.user
        notifications = xx_notification.objects.filter(user=user, is_shown=True).order_by('created_at').reverse()
        data = [
            {
                'id': notification.id,
                'message': notification.message,
                'is_read': notification.is_read,
                'created_at': notification.created_at,
                'is_shown': notification.is_shown,
                'is_system_read': notification.is_system_read
            } for notification in notifications
        ]
        return Response({
            'notifications': data
        })
class Read_Notification(APIView):
    """Mark a notification as read"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            notification_id = request.query_params.get('notification_id')
            notification = xx_notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Notification marked as read.'})
        except xx_notification.DoesNotExist:
            return Response({'message': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
class Read_All_Notification(APIView):
    """Mark a notification as read"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            notifications = xx_notification.objects.filter(user=request.user, is_read=False)
            for notification in notifications:
                notification.is_read = True
                notification.save()
            return Response({'message': 'Notification marked as read.'})
        except xx_notification.DoesNotExist:
            return Response({'message': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
class Delete_Nnotification(APIView):
    """Delete a specific notification"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            notification_id = request.query_params.get('notification_id')
            notification = xx_notification.objects.get(id=notification_id, user=request.user)
            notification.is_shown = False
            notification.save()
            return Response({'message': 'Notification deleted successfully.'})
        except xx_notification.DoesNotExist:
            return Response({'message': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)






# def execute_oracle_query(sql_query):
#         """Execute SQL query safely in Oracle database"""
#         # Security: Only allow SELECT statements
#         if not sql_query.strip().upper().startswith('SELECT'):
#             raise ValueError("Only SELECT queries are allowed for security reasons")
        
#         with connection.cursor() as cursor:
#             cursor.execute(sql_query)
            
#             # Get column names
#             columns = [col[0] for col in cursor.description]
            
#             # Fetch all results
#             rows = cursor.fetchall()
            
#             # Convert to list of dictionaries
#             results = []
#             for row in rows:
#                 row_dict = {}
#                 for i, value in enumerate(row):
#                     # Handle Oracle-specific data types
#                     if hasattr(value, 'read'):  # Handle CLOB/BLOB
#                         row_dict[columns[i]] = value.read()
#                     else:
#                         row_dict[columns[i]] = value
#                 results.append(row_dict)
            
#             return {
#                 'columns': columns,
#                 'data': results,
#                 'row_count': len(results)
#             }




# class testChatbot(APIView):
#     """Test chatbot functionality"""
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user_message = request.data.get('message', '')
#         if not user_message:
#             return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
#         # Example of using LLMQueryGenerator to generate a response
#         table_info_example = {
#             # User Management Models
#             "XX_USER": [
#                 "id", "username", "role", "is_active", "is_staff", 
#                 "can_transfer_budget", "user_level_id", "password", 
#                 "last_login", "is_superuser"
#             ],
#             "XX_USER_LEVEL": [
#                 "id", "name", "description", "level_order"
#             ],
#             "XX_NOTIFICATION": [
#                 "id", "user_id", "message", "is_read", "created_at", 
#                 "is_system_read", "is_shown"
#             ],
            
#             # Budget Management Models
#             "XX_BUDGET_TRANSFER": [
#                 "transaction_id", "transaction_date", "amount", "status", 
#                 "requested_by", "user_id", "request_date", "notes", 
#                 "description_x", "code", "gl_posting_status", "approvel_1", 
#                 "approvel_2", "approvel_3", "approvel_4", "approvel_1_date", 
#                 "approvel_2_date", "approvel_3_date", "approvel_4_date", 
#                 "status_level", "attachment", "fy", "group_id", "interface_id", 
#                 "reject_group_id", "reject_interface_id", "approve_group_id", 
#                 "approve_interface_id", "report", "type"
#             ],
#             "XX_BUDGET_TRANSFER_ATTACHMENT": [
#                 "attachment_id", "transaction_id", "file_name", "file_type", 
#                 "file_size", "file_data", "upload_date"
#             ],
#             "XX_BUDGET_TRANSFER_REJECT_REASON": [
#                 "id", "Transcation_id", "reason_text", "reject_date", "reject_by"
#             ],
            
#             # ADJD Transaction Models
#             "xx_AdjdTransactionTransfer": [
#                 "transfer_id", "cost_center_code", "account_name", 
#                 "approved_budget", "available_budget", "from_center", 
#                 "to_center", "transaction_id", "reason", "account_code", 
#                 "cost_center_name", "done", "encumbrance", "actual", "file"
#             ],
            
#             # Account and Entity Models
#             "XX_Account": [
#                 "id", "account", "parent", "alias_default"
#             ],
#             "XX_Entity": [
#                 "id", "entity", "parent", "alias_default"
#             ],
#             "XX_PivotFund": [
#                 "id", "entity", "account", "year", "actual", "fund", 
#                 "budget", "encumbrance"
#             ],
#             "XX_ADJD_TRANSACTION_AUDIT": [
#                 "id", "type", "transfer_id", "transcation_code", 
#                 "cost_center_code", "account_code"
#             ],
#             "XX_ACCOUNT_ENTITY_LIMIT": [
#                 "id", "account_id", "entity_id", "is_transer_allowed_for_source", 
#                 "is_transer_allowed_for_target", "is_transer_allowed", 
#                 "source_count", "target_count"
#             ],
            
#             # Relationships and common queries
#             "COMMON_JOINS": {
#                 "user_with_level": "XX_USER.user_level_id = XX_USER_LEVEL.id",
#                 "notifications_with_user": "XX_NOTIFICATION.user_id = XX_USER.id",
#                 "budget_transfer_with_user": "XX_BUDGET_TRANSFER.user_id = XX_USER.id",
#                 "adjd_transfer_with_budget": "xx_AdjdTransactionTransfer.transaction_id = XX_BUDGET_TRANSFER.transaction_id",
#                 "attachments_with_transfer": "XX_BUDGET_TRANSFER_ATTACHMENT.transaction_id = XX_BUDGET_TRANSFER.transaction_id",
#                 "reject_reasons_with_transfer": "XX_BUDGET_TRANSFER_REJECT_REASON.Transcation_id = XX_BUDGET_TRANSFER.transaction_id",
#                 "pivot_fund_entity_account": "XX_PivotFund.entity = XX_Entity.entity AND XX_PivotFund.account = XX_Account.account"
#             },
            
#             # Commonly used filters
#             "COMMON_FILTERS": {
#                 "active_users": "XX_USER.is_active = 1",
#                 "admin_users": "XX_USER.role = 'admin'",
#                 "users_can_transfer": "XX_USER.can_transfer_budget = 1",
#                 "unread_notifications": "XX_NOTIFICATION.is_read = 0",
#                 "pending_transfers": "XX_BUDGET_TRANSFER.status = 'pending'",
#                 "current_year_pivot": f"XX_PivotFund.year = {timezone.now().year}",
#                 "completed_adjd_transfers": "xx_AdjdTransactionTransfer.done = 1"
#             }
#         }
#         generator = LLMQueryGenerator(table_info_example)

#         sql_query = generator.generate_sql_query(user_message)

#         try:
#             query_results = execute_oracle_query(sql_query)
#             return Response({
#                 'generated_query': sql_query,
#                 'results': query_results,
#                 'message': 'Query executed successfully'
#             })
#         except Exception as e:
#             return Response({
#                 'generated_query': sql_query,
#                 'error': str(e),
#                 'message': 'Query execution failed'
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


