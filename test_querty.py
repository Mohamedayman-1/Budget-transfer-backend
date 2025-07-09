# import ollama

# class LLMQueryGenerator:
#     """
#     Example of using an LLM to generate SQL queries based on user requests and known table schema.
#     Replace 'YOUR_API_KEY' with your actual key or integrate your own LLM call.
#     """

#     def __init__(self, table_info):
#         """
#         table_info: dict containing table names and columns, e.g.,
#         {
#           "users": ["id", "name", "email"],
#           "orders": ["id", "user_id", "total"]
#         }
#         """
#         self.table_info = table_info
#         # Example: openai.api_key = "YOUR_API_KEY"

#     def generate_sql_query(self, user_request: str) -> str:
#         """
#         Sends user_request to the LLM along with the table schema, expecting an SQL statement in return.
#         """
#         # A typical prompt to guide the model to produce a valid SQL query:
#         prompt = (
#         "You are a SQL query generator for Oracle database. Here is the schema:\n"
#         + "\n".join([f"Table {t}: {', '.join(cols)}" for t, cols in self.table_info.items() if not t.startswith('COMMON')])
#         + "\n\nUser request: " + user_request
#         + "\n\nRules:"
#         + "\n- Generate ONLY a valid Oracle SQL SELECT query"
#         + "\n- Do NOT use markdown formatting or backticks"
#         + "\n- Do NOT use COMMON_FILTERS or COMMON_JOINS as tables"
#         + "\n- Use only the tables listed in the schema"
#         + "\n- End with semicolon"
#         + "\n\nSQL Query:"
#     )

#         # Using Ollama instead of OpenAI
#         response = ollama.chat(model='llama3', messages=[
#             {
#                 'role': 'user',
#                 'content': prompt,
#             },
#         ])
        
#         # Extract the SQL query from the response
#         sql_query = response['message']['content'].strip()
        
#         return sql_query

# # Example usage:
# if __name__ == "__main__":
#     table_info_example = {
#         "users": ["id", "name", "email"],
#         "orders": ["id", "user_id", "total"]
#     }
#     generator = LLMQueryGenerator(table_info_example)
#     user_input = input("Enter your request for data (e.g., 'Get all users with orders over $100'): ")
#     sql_query = generator.generate_sql_query(user_input)
#     print("Generated SQL Query:", sql_query)