from django.urls import path
from .views import RegisterView, LoginView, TokenExpiredView, ListUsersView, UpdateUserPermissionView, UserLevelListView, UserLevelCreateView, UpdateUserLevelView, UserUpdateView, UserDeleteView, UserLevelUpdateView, UserLevelDeleteView, UnRead_Notification,System_Notification,Get_All_Notification,Read_Notification,Read_All_Notification,Delete_Nnotification

app_name = 'user_management'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token-expired/', TokenExpiredView.as_view(), name='token-expired'),
    
    # User management endpoints
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('users/permission/<int:user_id>/', UpdateUserPermissionView.as_view(), name='update_user_permission'),
    path('users/update/', UserUpdateView.as_view(), name='user_update'),
    path('users/delete/', UserDeleteView.as_view(), name='user_delete'),



    # User level management endpoints
    path('levels/', UserLevelListView.as_view(), name='user-level-list'),
    path('levels/create/', UserLevelCreateView.as_view(), name='user-level-create'),
    path('levels/update/', UserLevelUpdateView.as_view(), name='level_update'),
    path('levels/delete/', UserLevelDeleteView.as_view(), name='level_delete'),


    # Notification management endpoints
    #
    path('Notifications/unread', UnRead_Notification.as_view(), name='unread-notifications'),
    path('Notifications/system', System_Notification.as_view(), name='system-notifications'),
    path('Notifications/get_all', Get_All_Notification.as_view(), name='all-notifications'),
    path('Notifications/read_one', Read_Notification.as_view(), name='read-notification'),
    path('Notifications/read_all', Read_All_Notification.as_view(), name='read-all-notifications'),
    path('Notifications/delete', Delete_Nnotification.as_view(), name='delete-notification'),
]
