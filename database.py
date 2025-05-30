import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
import os

class CakeShopDatabase:
    def __init__(self, db_path: str = "cake_shop.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Create tables if they don't exist and populate with initial data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                postcode TEXT NOT NULL,
                dob TEXT NOT NULL,
                first_line_address TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                status TEXT NOT NULL,
                items TEXT NOT NULL,  -- JSON string of item IDs
                quantity TEXT NOT NULL,  -- JSON string of quantities
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_protection_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                postcode TEXT NOT NULL,
                year_of_birth INTEGER NOT NULL,
                month_of_birth INTEGER NOT NULL,
                day_of_birth INTEGER NOT NULL,
                check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] == 0:
            self._populate_initial_data(cursor)
            conn.commit()
        
        conn.close()
    
    def _populate_initial_data(self, cursor):
        """Populate database with initial customer and order data"""
        initial_customers = [
            ("CUST001", "John Doe", "SW1A 1AA", "1990-01-01", "123 Main St", "07712345678", "john.doe@example.com"),
            ("CUST002", "Jane Smith", "E1 6AN", "1985-05-15", "456 High St", "07723456789", "jane.smith@example.com"),
        ]
        
        cursor.executemany('''
            INSERT INTO customers (customer_id, name, postcode, dob, first_line_address, phone_number, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', initial_customers)
        
        initial_orders = [
            ("ORD001", "CUST001", "Processing", '["C001"]', '[1]'),
            ("ORD002", "CUST002", "Shipped", '["C007", "C011"]', '[1, 2]'),
            ("ORD003", "CUST001", "Delivered", '["C015"]', '[1]'),
            ("ORD004", "CUST002", "Processing", '["C003", "C013", "C031"]', '[1, 1, 2]')
        ]
        
        cursor.executemany('''
            INSERT INTO orders (order_id, customer_id, status, items, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', initial_orders)
    
    
    def create_customer(self, first_name: str, surname: str, year_of_birth: int, 
                       month_of_birth: int, day_of_birth: int, postcode: str, 
                       first_line_address: str, phone_number: str, email: str) -> str:
        """Create a new customer in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        customer_id = f"CUST{customer_count + 1:03d}"
        
        dob = f"{year_of_birth}-{month_of_birth:02d}-{day_of_birth:02d}"
        full_name = f"{first_name} {surname}"
        
        try:
            cursor.execute('''
                INSERT INTO customers (customer_id, name, postcode, dob, first_line_address, phone_number, email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, full_name, postcode, dob, first_line_address, phone_number, email))
            
            conn.commit()
            conn.close()
            return f"Customer registered, with customer_id {customer_id}"
        
        except sqlite3.Error as e:
            conn.close()
            return f"Error creating customer: {str(e)}"
    
    def get_customer_by_details(self, name: str, postcode: str, year_of_birth: int, 
                               month_of_birth: int, day_of_birth: int) -> Optional[Dict]:
        """Get customer by data protection check details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        dob = f"{year_of_birth}-{month_of_birth:02d}-{day_of_birth:02d}"
        
        cursor.execute('''
            SELECT customer_id, name, postcode, dob, first_line_address, phone_number, email
            FROM customers 
            WHERE LOWER(name) = LOWER(?) AND LOWER(postcode) = LOWER(?) AND dob = ?
        ''', (name, postcode, dob))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "customer_id": result[0],
                "name": result[1],
                "postcode": result[2],
                "dob": result[3],
                "first_line_address": result[4],
                "phone_number": result[5],
                "email": result[6]
            }
        return None
    
    def get_all_customers(self) -> List[Dict]:
        """Get all customers from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT customer_id, name, postcode, dob, first_line_address, phone_number, email
            FROM customers
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        customers = []
        for row in results:
            customers.append({
                "customer_id": row[0],
                "name": row[1],
                "postcode": row[2],
                "dob": row[3],
                "first_line_address": row[4],
                "phone_number": row[5],
                "email": row[6]
            })
        
        return customers
    
    
    def create_order(self, items: Dict[str, int], customer_id: str) -> str:
        """Create a new order in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        order_id = f"ORD{order_count + 1:03d}"
        
        items_json = json.dumps(list(items.keys()))
        quantities_json = json.dumps(list(items.values()))
        
        try:
            cursor.execute('''
                INSERT INTO orders (order_id, customer_id, status, items, quantity)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, customer_id, "Waiting for payment", items_json, quantities_json))
            
            conn.commit()
            conn.close()
            return f"Order with id {order_id} has been placed successfully"
        
        except sqlite3.Error as e:
            conn.close()
            return f"Error creating order: {str(e)}"
    
    def get_customer_orders(self, customer_id: str) -> List[Dict]:
        """Get all orders for a specific customer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT order_id, customer_id, status, items, quantity, created_at
            FROM orders 
            WHERE customer_id = ?
        ''', (customer_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return []
        
        orders = []
        for row in results:
            orders.append({
                "order_id": row[0],
                "customer_id": row[1],
                "status": row[2],
                "items": json.loads(row[3]),
                "quantity": json.loads(row[4]),
                "created_at": row[5]
            })
        
        return orders
    
    def get_all_orders(self) -> List[Dict]:
        """Get all orders from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT order_id, customer_id, status, items, quantity, created_at
            FROM orders
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in results:
            orders.append({
                "order_id": row[0],
                "customer_id": row[1],
                "status": row[2],
                "items": json.loads(row[3]),
                "quantity": json.loads(row[4]),
                "created_at": row[5]
            })
        
        return orders
    
    def update_order_status(self, order_id: str, new_status: str) -> str:
        """Update order status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE orders 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ?
            ''', (new_status, order_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return f"Order {order_id} status updated to {new_status}"
            else:
                conn.close()
                return f"Order {order_id} not found"
        
        except sqlite3.Error as e:
            conn.close()
            return f"Error updating order: {str(e)}"
    
    
    def log_data_protection_check(self, name: str, postcode: str, year_of_birth: int, 
                                 month_of_birth: int, day_of_birth: int):
        """Log a data protection check attempt"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO data_protection_checks (name, postcode, year_of_birth, month_of_birth, day_of_birth)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, postcode, year_of_birth, month_of_birth, day_of_birth))
        
        conn.commit()
        conn.close()
    
    def get_data_protection_checks(self) -> List[Dict]:
        """Get all data protection check logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, postcode, year_of_birth, month_of_birth, day_of_birth, check_timestamp
            FROM data_protection_checks
            ORDER BY check_timestamp DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        checks = []
        for row in results:
            checks.append({
                "name": row[0],
                "postcode": row[1],
                "year_of_birth": row[2],
                "month_of_birth": row[3],
                "day_of_birth": row[4],
                "check_timestamp": row[5]
            })
        
        return checks

db = CakeShopDatabase()
