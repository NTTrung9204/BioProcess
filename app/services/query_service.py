from app.repositories import query_database

def executive_query(custom_query):
    return query_database(custom_query) 