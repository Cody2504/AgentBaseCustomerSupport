from langchain_core.tools import tool
from typing import List, Dict
from vector_store import CakeShopVectorStore
from database import db
import json
import os

vector_store = CakeShopVectorStore()

@tool
def query_knowledge_base(query: str) -> List[Dict[str, str]]:
    """
    Look up information in the knowledge base to help with answering customer questions and getting information on business processes.
    
    Args:
        query (str): Question to ask the knowledge base.

    Return:
        List[Dict[str, str]]: Relevant questions and answers from the knowledge base.
    """
    return vector_store.query_faqs(query)


@tool
def search_for_product_recommendations(description: str):
    """
    Look up information in the knowledge base to help with product recommendation for customers. For example:

    "Cakes suitable for birthdays, maybe with chocolate flavor"
    "A large cake with elegant design for a wedding"
    "An affordable cake with fruit flavors for a party"
    
    Args:
        query (str): Description of product features

    Return:
        List[Dict[str, str]]: Relevant products.
    """    
    return vector_store.query_inventories(description)

@tool
def data_protection_check(name: str, postcode: str, year_of_birth: int, month_of_birth: int, day_of_birth: int) -> Dict:
    """
    Perform a data protection check against a customer to retrieve customer details.

    Args:
        name (str): Customer first and last name
        postcode (str): Customer registered address
        year_of_birth (int): The year the customer was born
        month_of_birth (int): The month the customer was born
        day_of_birth (int): The day the customer was born

    Returns:
        Dict: Customer details (name, postcode, dob, customer_id, first_line_address, email)
    """
    # Log the data protection check attempt
    db.log_data_protection_check(name, postcode, year_of_birth, month_of_birth, day_of_birth)
    
    # Get customer from database
    customer = db.get_customer_by_details(name, postcode, year_of_birth, month_of_birth, day_of_birth)
    
    if customer:
        return f"DPA check passed - Retrieved customer details:\n{customer}"
    else:
        return "DPA check failed, no customer with these details found"

@tool
def create_new_customer(first_name: str, surname: str, year_of_birth: int, month_of_birth: int, day_of_birth: int, postcode: str, first_line_of_address: str, phone_number: str, email: str) -> str:
    """
    Creates a customer profile, so that they can place orders.

    Args:
        first_name (str): Customers first name
        surname (str): Customers surname
        year_of_birth (int): Year customer was born
        month_of_birth (int): Month customer was born
        day_of_birth (int): Day customer was born
        postcode (str): Customer's postcode
        first_line_address (str): Customer's first line of address
        phone_number (str): Customer's phone number
        email (str): Customer's email address

    Returns:
        str: Confirmation that the profile has been created or any issues with the inputs
    """
    if len(phone_number) != 11:
        return "Phone number must be 11 digits"
    
    return db.create_customer(first_name, surname, year_of_birth, month_of_birth, 
                             day_of_birth, postcode, first_line_of_address, phone_number, email)
    
@tool
def retrieve_existing_customer_orders(customer_id: str) -> List[Dict]:
    """
    Retrieves the orders associated with the customer, including their status, items and ids

    Args:
        customer_id (str): Customer unique id associated with the order

    Returns:
        List[Dict]: All the orders associated with the customer_id passed in
    """
    customer_orders = db.get_customer_orders(customer_id)
    if not customer_orders:
        return f"No orders associated with this customer id: {customer_id}"
    return customer_orders

with open('cake_inventory.json', 'r') as f:
    inventory_database = json.load(f)
@tool
def place_order(items: Dict[str, int], customer_id: str) -> str:
    """
    Places an order for the requested items, and for the required quantities.

    Args:
        items (Dict[str, int]): Dictionary of items to order, with item id as the key and the quantity of that item as the value.
        customer_id (str): The customer to place the order for

    Returns:
        str: Message indicating that the order has been placed, or, it hasnt been placed due to an issue 
    """
    # Check that the item ids are valid 
    # Check that the quantities of items are valid
    availability_messages = []
    valid_item_ids = [
        item['id'] for item in inventory_database
    ]
    for item_id, quantity in items.items():
        if item_id not in valid_item_ids:
            availability_messages.append(f'Item with id {item_id} is not found in the inventory')
        else:
            inventory_item = [item for item in inventory_database if item['id'] == item_id][0]
            if quantity > inventory_item['quantity']:
                availability_messages.append(f'There is insufficient quantity in the inventory for this item {inventory_item["name"]}\nAvailable: {inventory_item["quantity"]}\nRequested: {quantity}')
    if availability_messages:
        return "Order cannot be placed due to the following issues: \n" + '\n'.join(availability_messages)

    # Create order in database
    result = db.create_order(items, customer_id)
    
    # Update the inventory if order was created successfully
    if "successfully" in result:
        for item_id, quantity in items.items():
            inventory_item = [item for item in inventory_database if item['id'] == item_id][0]
            inventory_item['quantity'] -= quantity
    
    return result

def get_all_customers() -> List[Dict]:
    """
    Retrieve all customers from the database.
    
    Returns:
        List[Dict]: List of all customers with their details
    """
    return db.get_all_customers()

def get_data_protection_check_logs() -> List[Dict]:
    """
    Retrieve all data protection check logs from the database.
    
    Returns:
        List[Dict]: List of all DPA check attempts with timestamps
    """
    return db.get_data_protection_checks()