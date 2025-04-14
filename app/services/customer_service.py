from app.repositories import (
    create_customer_table, get_all_customers, get_customer_by_name, 
    add_customer, update_customer, delete_customer, search_customers
)

def initialize_customer_db():
    return create_customer_table()

def get_customers_service():
    return get_all_customers()

def get_customer_service(cust_name):
    return get_customer_by_name(cust_name)

def add_customer_service(cust_name, contact_infor, address, country):
    if not cust_name or len(cust_name.strip()) < 6 or len(cust_name.strip()) > 18:
        return False, "Customer name must be between 6-18 characters"
    
    return add_customer(cust_name.strip(), contact_infor, address, country)

def update_customer_service(cust_name, contact_infor, address, country):
    customer = get_customer_by_name(cust_name)
    if not customer:
        return False, "Customer not found"
    
    return update_customer(cust_name, contact_infor, address, country)

def delete_customer_service(cust_name):
    return delete_customer(cust_name)

def search_customers_service(search_term):
    if not search_term or len(search_term) < 2:
        return []
    
    return search_customers(search_term) 