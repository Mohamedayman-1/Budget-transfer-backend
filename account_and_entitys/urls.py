from django.urls import path
from .views import (
    AccountListView, AccountCreateView, AccountDetailView, AccountUpdateView, AccountDeleteView,
    EntityListView, EntityCreateView, EntityDetailView, EntityUpdateView, EntityDeleteView,
    PivotFundListView, PivotFundCreateView, PivotFundDetailView, PivotFundUpdateView, PivotFundDeleteView,
    AdjdTransactionAuditListView, AdjdTransactionAuditCreateView, AdjdTransactionAuditDetailView, 
    AdjdTransactionAuditUpdateView, AdjdTransactionAuditDeleteView, list_ACCOUNT_ENTITY_LIMIT,UpdateAccountEntityLimit,DeleteAccountEntityLimit,
    MainCurrencyListView, MainCurrencyCreateView, MainCurrencyDetailView, MainCurrencyUpdateView, MainCurrencyDeleteView,
    MainRoutesNameListView, MainRoutesNameCreateView, MainRoutesNameDetailView, MainRoutesNameUpdateView, MainRoutesNameDeleteView
)

urlpatterns = [
    # Account URLs
    path('accounts/', AccountListView.as_view(), name='account-list'),
    path('accounts/create/', AccountCreateView.as_view(), name='account-create'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account-detail'),
    path('accounts/<int:pk>/update/', AccountUpdateView.as_view(), name='account-update'),
    path('accounts/<int:pk>/delete/', AccountDeleteView.as_view(), name='account-delete'),
    
    # Entity URLs
    path('entities/', EntityListView.as_view(), name='entity-list'),
    path('entities/create/', EntityCreateView.as_view(), name='entity-create'),
    path('entities/<int:pk>/', EntityDetailView.as_view(), name='entity-detail'),
    path('entities/<int:pk>/update/', EntityUpdateView.as_view(), name='entity-update'),
    path('entities/<int:pk>/delete/', EntityDeleteView.as_view(), name='entity-delete'),
    
    # PivotFund URLs
    path('pivot-funds/', PivotFundListView.as_view(), name='pivotfund-list'),
    path('pivot-funds/create/', PivotFundCreateView.as_view(), name='pivotfund-create'),
    path('pivot-funds/getdetail/', PivotFundDetailView.as_view(), name='pivotfund-detail'),
    path('pivot-funds/<int:pk>/update/', PivotFundUpdateView.as_view(), name='pivotfund-update'),
    path('pivot-funds/<int:pk>/delete/', PivotFundDeleteView.as_view(), name='pivotfund-delete'),
    
    # ADJD Transaction Audit URLs
    path('transaction-audits/', AdjdTransactionAuditListView.as_view(), name='transaction-audit-list'),
    path('transaction-audits/create/', AdjdTransactionAuditCreateView.as_view(), name='transaction-audit-create'),
    path('transaction-audits/<int:pk>/', AdjdTransactionAuditDetailView.as_view(), name='transaction-audit-detail'),
    path('transaction-audits/<int:pk>/update/', AdjdTransactionAuditUpdateView.as_view(), name='transaction-audit-update'),
    path('transaction-audits/<int:pk>/delete/', AdjdTransactionAuditDeleteView.as_view(), name='transaction-audit-delete'),

    # Fix the URL for list_ACCOUNT_ENTITY_LIMIT view
    path('account-entity-limit/list/', list_ACCOUNT_ENTITY_LIMIT.as_view(), name='account-entity-limits'),
    
    # Update and Delete URLs for Account Entity Limit
    path('account-entity-limit/update/', UpdateAccountEntityLimit.as_view(), name='update_limit'),
    path('account-entity-limit/delete/', DeleteAccountEntityLimit.as_view(), name='delete_limit'),
    
    # Main Currency URLs
    path('main-currencies/', MainCurrencyListView.as_view(), name='main-currency-list'),
    path('main-currencies/create/', MainCurrencyCreateView.as_view(), name='main-currency-create'),
    path('main-currencies/<int:pk>/', MainCurrencyDetailView.as_view(), name='main-currency-detail'),
    path('main-currencies/<int:pk>/update/', MainCurrencyUpdateView.as_view(), name='main-currency-update'),
    path('main-currencies/<int:pk>/delete/', MainCurrencyDeleteView.as_view(), name='main-currency-delete'),
    
    # Main Routes Name URLs
    path('main-routes/', MainRoutesNameListView.as_view(), name='main-routes-list'),
    path('main-routes/create/', MainRoutesNameCreateView.as_view(), name='main-routes-create'),
    path('main-routes/<int:pk>/', MainRoutesNameDetailView.as_view(), name='main-routes-detail'),
    path('main-routes/<int:pk>/update/', MainRoutesNameUpdateView.as_view(), name='main-routes-update'),
    path('main-routes/<int:pk>/delete/', MainRoutesNameDeleteView.as_view(), name='main-routes-delete'),
]
