from django.db import connection


def execute_oracle_query(sql_query):
    """Execute SQL query safely in Oracle database"""
    # Security: Only allow SELECT statements
    if not sql_query.strip().upper().startswith('SELECT'):
        raise ValueError("Only SELECT queries are allowed for security reasons")
    
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        
        # Get column names
        columns = [col[0] for col in cursor.description]
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        results = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                # Handle Oracle-specific data types
                if hasattr(value, 'read'):  # Handle CLOB/BLOB
                    row_dict[columns[i]] = value.read()
                else:
                    row_dict[columns[i]] = value
            results.append(row_dict)
        
        return {
            'columns': columns,
            'data': results,
            'row_count': len(results)
        }

print(execute_oracle_query("SELECT table_name FROM user_tables;"))