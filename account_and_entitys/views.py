from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import XX_Account, XX_Entity, XX_PivotFund, XX_TransactionAudit, XX_ACCOUNT_ENTITY_LIMIT, MainCurrency, MainRoutesName
from .serializers import AccountSerializer, EntitySerializer, PivotFundSerializer, TransactionAuditSerializer, AccountEntityLimitSerializer, MainCurrencySerializer, MainRoutesNameSerializer

class EntityPagination(PageNumberPagination):
    """Pagination class for entities and accounts"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# Account views
class AccountListView(APIView):
    """List all accounts"""
    permission_classes = [IsAuthenticated]
    pagination_class = EntityPagination
    
    def get(self, request):
        accounts = XX_Account.objects.all().order_by('account')
        serializer = AccountSerializer(accounts, many=True)
        
        # Return all data directly without pagination
        return Response({
            'message': 'Accounts retrieved successfully.',
            'data': serializer.data
        })

class AccountCreateView(APIView):
    """Create a new account"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save()
            return Response({
                'message': 'Account created successfully.',
                'data': AccountSerializer(account).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Failed to create account.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class AccountDetailView(APIView):
    """Retrieve a specific account"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_Account.objects.get(pk=pk)
        except XX_Account.DoesNotExist:
            return None
    
    def get(self, request, pk):
        account = self.get_object(pk)
        if account is None:
            return Response({
                'message': 'Account not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = AccountSerializer(account)
        return Response({
            'message': 'Account details retrieved successfully.',
            'data': serializer.data
        })

class AccountUpdateView(APIView):
    """Update a specific account"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_Account.objects.get(pk=pk)
        except XX_Account.DoesNotExist:
            return None
    
    def put(self, request, pk):
        account = self.get_object(pk)
        if account is None:
            return Response({
                'message': 'Account not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = AccountSerializer(account, data=request.data)
        if serializer.is_valid():
            updated_account = serializer.save()
            return Response({
                'message': 'Account updated successfully.',
                'data': AccountSerializer(updated_account).data
            })
        return Response({
            'message': 'Failed to update account.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class AccountDeleteView(APIView):
    """Delete a specific account"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_Account.objects.get(pk=pk)
        except XX_Account.DoesNotExist:
            return None
    
    def delete(self, request, pk):
        account = self.get_object(pk)
        if account is None:
            return Response({
                'message': 'Account not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        account.delete()
        return Response({
            'message': 'Account deleted successfully.'
        }, status=status.HTTP_200_OK)

# Entity views
class EntityListView(APIView):
    """List all entities"""
    permission_classes = [IsAuthenticated]
    pagination_class = EntityPagination
    
    def get(self, request):
        entities = XX_Entity.objects.all().order_by('entity')
        
        serializer = EntitySerializer(entities, many=True)
        
        return Response({
            'message': 'Accounts retrieved successfully.',
            'data': serializer.data
        })

class EntityCreateView(APIView):
    """Create a new entity"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = EntitySerializer(data=request.data)
        if serializer.is_valid():
            entity = serializer.save()
            return Response({
                'message': 'Entity created successfully.',
                'data': EntitySerializer(entity).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Failed to create entity.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class EntityDetailView(APIView):
    """Retrieve a specific entity"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_Entity.objects.get(pk=pk)
        except XX_Entity.DoesNotExist:
            return None
    
    def get(self, request, pk):
        entity = self.get_object(pk)
        if entity is None:
            return Response({
                'message': 'Entity not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = EntitySerializer(entity)
        return Response({
            'message': 'Entity details retrieved successfully.',
            'data': serializer.data
        })

class EntityUpdateView(APIView):
    """Update a specific entity"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_Entity.objects.get(pk=pk)
        except XX_Entity.DoesNotExist:
            return None
    
    def put(self, request, pk):
        entity = self.get_object(pk)
        if entity is None:
            return Response({
                'message': 'Entity not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = EntitySerializer(entity, data=request.data)
        if serializer.is_valid():
            updated_entity = serializer.save()
            return Response({
                'message': 'Entity updated successfully.',
                'data': EntitySerializer(updated_entity).data
            })
        return Response({
            'message': 'Failed to update entity.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class EntityDeleteView(APIView):
    """Delete a specific entity"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_Entity.objects.get(pk=pk)
        except XX_Entity.DoesNotExist:
            return None
    
    def delete(self, request, pk):
        entity = self.get_object(pk)
        if entity is None:
            return Response({
                'message': 'Entity not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        entity.delete()
        return Response({
            'message': 'Entity deleted successfully.'
        }, status=status.HTTP_200_OK)

# PivotFund views
class PivotFundListView(APIView):
    """List all pivot funds"""
    permission_classes = [IsAuthenticated]
    pagination_class = EntityPagination
    
    def get(self, request):
        # Allow filtering by entity, account, and year
        entity_id = request.query_params.get('entity')
        account_id = request.query_params.get('account')
        year = request.query_params.get('year')
        
        pivot_funds = XX_PivotFund.objects.all()
        
        if entity_id:
            pivot_funds = pivot_funds.filter(entity=entity_id)
        if account_id:
            pivot_funds = pivot_funds.filter(account=account_id)
        if year:
            pivot_funds = pivot_funds.filter(year=year)
        
        # Order by year, entity, account
        pivot_funds = pivot_funds.order_by('-year', 'entity__entity', 'account__account')
        
        # Handle pagination
        paginator = self.pagination_class()
        paginated_funds = paginator.paginate_queryset(pivot_funds, request)
        serializer = PivotFundSerializer(paginated_funds, many=True)
        
        return paginator.get_paginated_response(serializer.data)

class PivotFundCreateView(APIView):
    """Create a new pivot fund"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Handle batch creation
        if isinstance(request.data, list):
            created_funds = []
            errors = []
            
            for index, fund_data in enumerate(request.data):
                serializer = PivotFundSerializer(data=fund_data)
                if serializer.is_valid():
                    fund = serializer.save()
                    created_funds.append(PivotFundSerializer(fund).data)
                else:
                    errors.append({
                        'index': index,
                        'errors': serializer.errors,
                        'data': fund_data
                    })
            
            response_data = {
                'message': f'Created {len(created_funds)} pivot funds, with {len(errors)} errors.',
                'created': created_funds,
                'errors': errors
            }
            
            if errors and not created_funds:
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            elif errors:
                return Response(response_data, status=status.HTTP_207_MULTI_STATUS)
            else:
                return Response(response_data, status=status.HTTP_201_CREATED)
        
        # Handle single creation
        else:
            serializer = PivotFundSerializer(data=request.data)
            if serializer.is_valid():
                fund = serializer.save()
                return Response({
                    'message': 'Pivot fund created successfully.',
                    'data': PivotFundSerializer(fund).data
                }, status=status.HTTP_201_CREATED)
            return Response({
                'message': 'Failed to create pivot fund.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class PivotFundDetailView(APIView):
    """Retrieve a specific pivot fund"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, entity,account):
        try:
           
            return XX_PivotFund.objects.get(entity=entity,account=account)
        
        except XX_PivotFund.DoesNotExist:
            

            return None
    
    def get(self, request):

        entity=request.query_params.get('entity_id')
        account=request.query_params.get('account_id')
        print(entity,account)
        pivot_fund = self.get_object(entity,account)

        if pivot_fund is None:
            return Response({
                'message': 'Pivot fund not found.'
            }, status=status.HTTP_200_OK)
        serializer = PivotFundSerializer(pivot_fund)
        return Response({
            'message': 'Pivot fund details retrieved successfully.',
            'data': serializer.data
        })

class PivotFundUpdateView(APIView):
    """Update a specific pivot fund"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_PivotFund.objects.get(pk=pk)
        except XX_PivotFund.DoesNotExist:
            return None
    
    def put(self, request, pk):
        pivot_fund = self.get_object(pk)
        if pivot_fund is None:
            return Response({
                'message': 'Pivot fund not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = PivotFundSerializer(pivot_fund, data=request.data)
        if serializer.is_valid():
            updated_fund = serializer.save()
            return Response({
                'message': 'Pivot fund updated successfully.',
                'data': PivotFundSerializer(updated_fund).data
            })
        return Response({
            'message': 'Failed to update pivot fund.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class PivotFundDeleteView(APIView):
    """Delete a specific pivot fund"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_PivotFund.objects.get(pk=pk)
        except XX_PivotFund.DoesNotExist:
            return None
    
    def delete(self, request, pk):
        pivot_fund = self.get_object(pk)
        if pivot_fund is None:
            return Response({
                'message': 'Pivot fund not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        pivot_fund.delete()
        return Response({
            'message': 'Pivot fund deleted successfully.'
        }, status=status.HTTP_200_OK)
    
# ADJD Transaction Audit views 

class AdjdTransactionAuditListView(APIView):
    """List all ADJD transaction audit records"""
    permission_classes = [IsAuthenticated]
    pagination_class = EntityPagination
    
    def get(self, request):
        audit_records = XX_TransactionAudit.objects.all().order_by('-id')
        
        # Handle pagination
        paginator = self.pagination_class()
        paginated_records = paginator.paginate_queryset(audit_records, request)
        serializer = TransactionAuditSerializer(paginated_records, many=True)
        
        return paginator.get_paginated_response(serializer.data)

class AdjdTransactionAuditCreateView(APIView):
    """Create a new ADJD transaction audit record"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = TransactionAuditSerializer(data=request.data)
        if serializer.is_valid():
            audit_record = serializer.save()
            return Response({
                'message': 'Audit record created successfully.',
                'data': TransactionAuditSerializer(audit_record).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Failed to create audit record.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class AdjdTransactionAuditDetailView(APIView):
    """Retrieve a specific ADJD transaction audit record"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_TransactionAudit.objects.get(pk=pk)
        except XX_TransactionAudit.DoesNotExist:
            return None
    
    def get(self, request, pk):
        audit_record = self.get_object(pk)
        if audit_record is None:
            return Response({
                'message': 'Audit record not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = TransactionAuditSerializer(audit_record)
        return Response({
            'message': 'Audit record details retrieved successfully.',
            'data': serializer.data
        })

class AdjdTransactionAuditUpdateView(APIView):
    """Update a specific ADJD transaction audit record"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_TransactionAudit.objects.get(pk=pk)
        except XX_TransactionAudit.DoesNotExist:
            return None
    
    def put(self, request, pk):
        audit_record = self.get_object(pk)
        if audit_record is None:
            return Response({
                'message': 'Audit record not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = TransactionAuditSerializer(audit_record, data=request.data)
        if serializer.is_valid():
            updated_record = serializer.save()
            return Response({
                'message': 'Audit record updated successfully.',
                'data': TransactionAuditSerializer(updated_record).data
            })
        return Response({
            'message': 'Failed to update audit record.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class AdjdTransactionAuditDeleteView(APIView):
    """Delete a specific ADJD transaction audit record"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return XX_TransactionAudit.objects.get(pk=pk)
        except XX_TransactionAudit.DoesNotExist:
            return None
    
    def delete(self, request, pk):
        audit_record = self.get_object(pk)
        if audit_record is None:
            return Response({
                'message': 'Audit record not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        audit_record.delete()
        return Response({
            'message': 'Audit record deleted successfully.'
        }, status=status.HTTP_200_OK)

class list_ACCOUNT_ENTITY_LIMIT(APIView):
    """List all ADJD transaction audit records"""
    permission_classes = [IsAuthenticated]
    pagination_class = EntityPagination
    
    def get(self, request):
        # Change "enity_id" to "entity_id"
        entity_id = request.query_params.get('cost_center')

        audit_records = XX_ACCOUNT_ENTITY_LIMIT.objects.filter(
            entity_id=entity_id
        ).order_by('-id')
        
        # Handle pagination
        paginator = self.pagination_class()
        paginated_records = paginator.paginate_queryset(audit_records, request)
        serializer = AccountEntityLimitSerializer(paginated_records, many=True)

        data = [
            {
                'id': record["id"],
                'account': record["account_id"],
                'is_transer_allowed_for_source': record["is_transer_allowed_for_source"],
                'is_transer_allowed_for_target': record["is_transer_allowed_for_target"],
                'is_transer_allowed': record["is_transer_allowed"],
                'source_count': record["source_count"],
                'target_count': record["target_count"],
            }
            for record in serializer.data
        ]
        
        return paginator.get_paginated_response(data)

class UpdateAccountEntityLimit(APIView):
    """Update a specific account entity limit."""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return XX_ACCOUNT_ENTITY_LIMIT.objects.get(pk=pk)
        except XX_ACCOUNT_ENTITY_LIMIT.DoesNotExist:
            return None

    def put(self, request):

        pk=request.query_params.get('pk')
        limit_record = self.get_object(pk)
        if limit_record is None:
            return Response({'message': 'Limit record not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AccountEntityLimitSerializer(limit_record, data=request.data)
        if serializer.is_valid():
            updated_record = serializer.save()
            return Response({
                'message': 'Limit record updated successfully.',
                'data': AccountEntityLimitSerializer(updated_record).data
            })
        return Response({'message': 'Failed to update limit record.', 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountEntityLimit(APIView):
    """Delete a specific account entity limit."""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return XX_ACCOUNT_ENTITY_LIMIT.objects.get(pk=pk)
        except XX_ACCOUNT_ENTITY_LIMIT.DoesNotExist:
            return None

    def delete(self, request, pk):
        limit_record = self.get_object(pk)
        if limit_record is None:
            return Response({'message': 'Limit record not found.'}, status=status.HTTP_404_NOT_FOUND)
        limit_record.delete()
        return Response({'message': 'Limit record deleted successfully.'}, status=status.HTTP_200_OK)

# MainCurrency views
class MainCurrencyListView(APIView):
    """List all main currencies"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        currencies = MainCurrency.objects.all().order_by('name')
        serializer = MainCurrencySerializer(currencies, many=True)
        
        return Response({
            'message': 'Main currencies retrieved successfully.',
            'data': serializer.data
        })

class MainCurrencyCreateView(APIView):
    """Create a new main currency"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = MainCurrencySerializer(data=request.data)
        if serializer.is_valid():
            currency = serializer.save()
            return Response({
                'message': 'Main currency created successfully.',
                'data': MainCurrencySerializer(currency).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Failed to create main currency.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class MainCurrencyDetailView(APIView):
    """Retrieve a specific main currency"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return MainCurrency.objects.get(pk=pk)
        except MainCurrency.DoesNotExist:
            return None
    
    def get(self, request, pk):
        currency = self.get_object(pk)
        if currency is None:
            return Response({
                'message': 'Main currency not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = MainCurrencySerializer(currency)
        return Response({
            'message': 'Main currency details retrieved successfully.',
            'data': serializer.data
        })

class MainCurrencyUpdateView(APIView):
    """Update a specific main currency"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return MainCurrency.objects.get(pk=pk)
        except MainCurrency.DoesNotExist:
            return None
    
    def put(self, request, pk):
        currency = self.get_object(pk)
        if currency is None:
            return Response({
                'message': 'Main currency not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = MainCurrencySerializer(currency, data=request.data)
        if serializer.is_valid():
            updated_currency = serializer.save()
            return Response({
                'message': 'Main currency updated successfully.',
                'data': MainCurrencySerializer(updated_currency).data
            })
        return Response({
            'message': 'Failed to update main currency.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class MainCurrencyDeleteView(APIView):
    """Delete a specific main currency"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return MainCurrency.objects.get(pk=pk)
        except MainCurrency.DoesNotExist:
            return None
    
    def delete(self, request, pk):
        currency = self.get_object(pk)
        if currency is None:
            return Response({
                'message': 'Main currency not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        currency.delete()
        return Response({
            'message': 'Main currency deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)


# MainRoutesName views
class MainRoutesNameListView(APIView):
    """List all main routes names"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        routes = MainRoutesName.objects.all().order_by('english_name')
        serializer = MainRoutesNameSerializer(routes, many=True)
        
        return Response({
            'message': 'Main routes names retrieved successfully.',
            'data': serializer.data
        })

class MainRoutesNameCreateView(APIView):
    """Create a new main routes name"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = MainRoutesNameSerializer(data=request.data)
        if serializer.is_valid():
            route = serializer.save()
            return Response({
                'message': 'Main routes name created successfully.',
                'data': MainRoutesNameSerializer(route).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Failed to create main routes name.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class MainRoutesNameDetailView(APIView):
    """Retrieve a specific main routes name"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return MainRoutesName.objects.get(pk=pk)
        except MainRoutesName.DoesNotExist:
            return None
    
    def get(self, request, pk):
        route = self.get_object(pk)
        if route is None:
            return Response({
                'message': 'Main routes name not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = MainRoutesNameSerializer(route)
        return Response({
            'message': 'Main routes name details retrieved successfully.',
            'data': serializer.data
        })

class MainRoutesNameUpdateView(APIView):
    """Update a specific main routes name"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return MainRoutesName.objects.get(pk=pk)
        except MainRoutesName.DoesNotExist:
            return None
    
    def put(self, request, pk):
        route = self.get_object(pk)
        if route is None:
            return Response({
                'message': 'Main routes name not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = MainRoutesNameSerializer(route, data=request.data)
        if serializer.is_valid():
            updated_route = serializer.save()
            return Response({
                'message': 'Main routes name updated successfully.',
                'data': MainRoutesNameSerializer(updated_route).data
            })
        return Response({
            'message': 'Failed to update main routes name.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class MainRoutesNameDeleteView(APIView):
    """Delete a specific main routes name"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return MainRoutesName.objects.get(pk=pk)
        except MainRoutesName.DoesNotExist:
            return None
    
    def delete(self, request, pk):
        route = self.get_object(pk)
        if route is None:
            return Response({
                'message': 'Main routes name not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        route.delete()
        return Response({
            'message': 'Main routes name deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)

