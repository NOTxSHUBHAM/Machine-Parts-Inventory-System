"""
Machine Parts Inventory Manager 
"""

import json
import os
from datetime import datetime, timedelta
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from collections import defaultdict
import random
import hashlib
import csv
import shutil
import webbrowser

# ==================== DATA CLASSES ====================

class Part:
    def __init__(self, part_id, name, category, quantity, price, supplier, location, 
                 min_quantity=5, reorder_quantity=10, cost_price=0, sku=""):
        self.part_id = part_id
        self.name = name
        self.category = category
        self.quantity = quantity
        self.selling_price = price
        self.cost_price = cost_price
        self.supplier = supplier
        self.location = location
        self.min_quantity = min_quantity
        self.reorder_quantity = reorder_quantity
        self.sku = sku
        self.created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.total_sold = 0
        self.total_purchased = quantity
    
    def to_dict(self):
        return {
            'part_id': self.part_id, 'name': self.name, 'category': self.category,
            'quantity': self.quantity, 'selling_price': self.selling_price,
            'cost_price': self.cost_price, 'supplier': self.supplier,
            'location': self.location, 'min_quantity': self.min_quantity,
            'reorder_quantity': self.reorder_quantity, 'sku': self.sku,
            'created_date': self.created_date, 'last_updated': self.last_updated,
            'total_sold': self.total_sold, 'total_purchased': self.total_purchased
        }
    
    @classmethod
    def from_dict(cls, data):
        part = cls(data['part_id'], data['name'], data['category'], data['quantity'],
                   data['selling_price'], data['supplier'], data['location'],
                   data.get('min_quantity', 5), data.get('reorder_quantity', 10),
                   data.get('cost_price', 0), data.get('sku', ''))
        part.created_date = data.get('created_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        part.last_updated = data.get('last_updated', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        part.total_sold = data.get('total_sold', 0)
        part.total_purchased = data.get('total_purchased', part.quantity)
        return part
    
    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.selling_price) * 100
        return 0
    
    @property
    def stock_value(self):
        return self.quantity * self.cost_price
    
    @property
    def needs_reorder(self):
        return self.quantity <= self.min_quantity


class Transaction:
    def __init__(self, transaction_id, part_id, transaction_type, quantity, 
                 price, customer_name="", notes=""):
        self.transaction_id = transaction_id
        self.part_id = part_id
        self.transaction_type = transaction_type
        self.quantity = quantity
        self.price = price
        self.customer_name = customer_name
        self.notes = notes
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self):
        return {
            'transaction_id': self.transaction_id, 'part_id': self.part_id,
            'transaction_type': self.transaction_type, 'quantity': self.quantity,
            'price': self.price, 'customer_name': self.customer_name,
            'notes': self.notes, 'date': self.date
        }
    
    @classmethod
    def from_dict(cls, data):
        trans = cls(data['transaction_id'], data['part_id'], data['transaction_type'],
                    data['quantity'], data['price'], data.get('customer_name', ''),
                    data.get('notes', ''))
        trans.date = data.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return trans


class User:
    def __init__(self, username, password, role, name=""):
        self.username = username
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.role = role
        self.name = name
        self.created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self):
        return {
            'username': self.username, 'password_hash': self.password_hash,
            'role': self.role, 'name': self.name, 'created_date': self.created_date
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls(data['username'], '', data['role'], data.get('name', ''))
        user.password_hash = data['password_hash']
        user.created_date = data.get('created_date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return user


class Customer:
    def __init__(self, customer_id, name, phone="", email="", address=""):
        self.customer_id = customer_id
        self.name = name
        self.phone = phone
        self.email = email
        self.address = address
        self.total_purchases = 0
        self.total_spent = 0
    
    def to_dict(self):
        return {
            'customer_id': self.customer_id, 'name': self.name,
            'phone': self.phone, 'email': self.email, 'address': self.address,
            'total_purchases': self.total_purchases, 'total_spent': self.total_spent
        }
    
    @classmethod
    def from_dict(cls, data):
        cust = cls(data['customer_id'], data['name'], data.get('phone', ''),
                   data.get('email', ''), data.get('address', ''))
        cust.total_purchases = data.get('total_purchases', 0)
        cust.total_spent = data.get('total_spent', 0)
        return cust


class Supplier:
    def __init__(self, supplier_id, name, contact_person="", phone="", email="", address=""):
        self.supplier_id = supplier_id
        self.name = name
        self.contact_person = contact_person
        self.phone = phone
        self.email = email
        self.address = address
        self.total_purchases = 0
    
    def to_dict(self):
        return {
            'supplier_id': self.supplier_id, 'name': self.name,
            'contact_person': self.contact_person, 'phone': self.phone,
            'email': self.email, 'address': self.address,
            'total_purchases': self.total_purchases
        }
    
    @classmethod
    def from_dict(cls, data):
        sup = cls(data['supplier_id'], data['name'], data.get('contact_person', ''),
                  data.get('phone', ''), data.get('email', ''), data.get('address', ''))
        sup.total_purchases = data.get('total_purchases', 0)
        return sup


# ==================== INVENTORY MANAGER ====================

class InventoryManager:
    def __init__(self):
        # Create data directory
        os.makedirs("data", exist_ok=True)
        
        self.filename = "data/inventory.json"
        self.transactions_file = "data/transactions.json"
        self.users_file = "data/users.json"
        self.customers_file = "data/customers.json"
        self.suppliers_file = "data/suppliers.json"
        
        self.parts = {}
        self.transactions = []
        self.users = {}
        self.customers = {}
        self.suppliers = {}
        self.current_user = None
        
        self.load_all_data()
        
        if len(self.users) == 0:
            self.create_default_admin()
        
        if len(self.parts) == 0:
            self.create_demo_data()
    
    def create_default_admin(self):
        admin = User('admin', 'admin123', 'admin', 'System Administrator')
        self.users[admin.username] = admin
        self.save_users()
        print("Default admin created")
    
    def load_all_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.parts = {pid: Part.from_dict(p) for pid, p in data.items()}
            except:
                pass
        
        if os.path.exists(self.transactions_file):
            try:
                with open(self.transactions_file, 'r') as f:
                    data = json.load(f)
                    self.transactions = [Transaction.from_dict(t) for t in data]
            except:
                pass
        
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    self.users = {uid: User.from_dict(u) for uid, u in data.items()}
            except:
                pass
        
        if os.path.exists(self.customers_file):
            try:
                with open(self.customers_file, 'r') as f:
                    data = json.load(f)
                    self.customers = {cid: Customer.from_dict(c) for cid, c in data.items()}
            except:
                pass
        
        if os.path.exists(self.suppliers_file):
            try:
                with open(self.suppliers_file, 'r') as f:
                    data = json.load(f)
                    self.suppliers = {sid: Supplier.from_dict(s) for sid, s in data.items()}
            except:
                pass
    
    def save_all_data(self):
        self.save_inventory()
        self.save_transactions()
        self.save_users()
        self.save_customers()
        self.save_suppliers()
    
    def save_inventory(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump({pid: p.to_dict() for pid, p in self.parts.items()}, f, indent=2)
            return True
        except:
            return False
    
    def save_transactions(self):
        try:
            with open(self.transactions_file, 'w') as f:
                json.dump([t.to_dict() for t in self.transactions], f, indent=2)
            return True
        except:
            return False
    
    def save_users(self):
        try:
            with open(self.users_file, 'w') as f:
                json.dump({uid: u.to_dict() for uid, u in self.users.items()}, f, indent=2)
            return True
        except:
            return False
    
    def save_customers(self):
        try:
            with open(self.customers_file, 'w') as f:
                json.dump({cid: c.to_dict() for cid, c in self.customers.items()}, f, indent=2)
            return True
        except:
            return False
    
    def save_suppliers(self):
        try:
            with open(self.suppliers_file, 'w') as f:
                json.dump({sid: s.to_dict() for sid, s in self.suppliers.items()}, f, indent=2)
            return True
        except:
            return False
    
    def authenticate(self, username, password):
        if username in self.users:
            user = self.users[username]
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if user.password_hash == password_hash:
                self.current_user = user
                return True, user.role
        return False, None
    
    def add_part(self, part):
        if part.part_id in self.parts:
            return False, f"Part ID {part.part_id} already exists!"
        self.parts[part.part_id] = part
        self.save_inventory()
        return True, f"Part {part.name} added!"
    
    def update_part(self, part_id, **kwargs):
        if part_id not in self.parts:
            return False, "Part not found!"
        part = self.parts[part_id]
        for key, value in kwargs.items():
            if hasattr(part, key):
                setattr(part, key, value)
        part.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_inventory()
        return True, "Part updated!"
    
    def delete_part(self, part_id):
        if part_id not in self.parts:
            return False, "Part not found!"
        part_name = self.parts[part_id].name
        del self.parts[part_id]
        self.save_inventory()
        return True, f"{part_name} deleted!"
    
    def sell_part(self, part_id, quantity, customer_id="", price_override=None):
        if part_id not in self.parts:
            return False, None, "Part not found!"
        
        part = self.parts[part_id]
        if part.quantity < quantity:
            return False, None, f"Insufficient stock! Only {part.quantity} available."
        
        part.quantity -= quantity
        part.total_sold += quantity
        part.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sale_price = price_override if price_override else part.selling_price
        
        customer_name = ""
        if customer_id and customer_id in self.customers:
            customer = self.customers[customer_id]
            customer_name = customer.name
            customer.total_purchases += quantity
            customer.total_spent += quantity * sale_price
            self.save_customers()
        
        trans_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transaction = Transaction(trans_id, part_id, 'SALE', quantity, 
                                  sale_price, customer_name, f"Sold {quantity} units")
        self.transactions.insert(0, transaction)
        
        self.save_inventory()
        self.save_transactions()
        return True, transaction, f"Sold {quantity} x {part.name} for ${quantity * sale_price:,.2f}"
    
    def purchase_part(self, part_id, quantity, purchase_price):
        if part_id not in self.parts:
            return False, "Part not found!"
        
        part = self.parts[part_id]
        part.quantity += quantity
        part.total_purchased += quantity
        part.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        trans_id = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        transaction = Transaction(trans_id, part_id, 'PURCHASE', quantity,
                                  purchase_price, "", f"Purchased {quantity} units")
        self.transactions.insert(0, transaction)
        
        self.save_inventory()
        self.save_transactions()
        return True, f"Added {quantity} x {part.name}"
    
    def add_customer(self, customer):
        if customer.customer_id in self.customers:
            return False, "Customer ID exists!"
        self.customers[customer.customer_id] = customer
        self.save_customers()
        return True, "Customer added!"
    
    def add_supplier(self, supplier):
        if supplier.supplier_id in self.suppliers:
            return False, "Supplier ID exists!"
        self.suppliers[supplier.supplier_id] = supplier
        self.save_suppliers()
        return True, "Supplier added!"
    
    def get_dashboard_stats(self):
        total_parts = len(self.parts)
        total_value = sum(p.quantity * p.cost_price for p in self.parts.values())
        total_sales = sum(p.total_sold * p.selling_price for p in self.parts.values())
        low_stock = len([p for p in self.parts.values() if p.needs_reorder])
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_sales = sum(t.quantity * t.price for t in self.transactions 
                         if t.transaction_type == 'SALE' and t.date.startswith(today))
        
        return {
            'total_parts': total_parts, 'total_value': total_value,
            'total_sales': total_sales, 'low_stock': low_stock,
            'today_sales': today_sales, 'total_transactions': len(self.transactions),
            'total_customers': len(self.customers), 'total_suppliers': len(self.suppliers)
        }
    
    def get_reorder_list(self):
        return [p for p in self.parts.values() if p.needs_reorder]
    
    def get_top_selling_parts(self, limit=5):
        return sorted(self.parts.values(), key=lambda x: x.total_sold, reverse=True)[:limit]
    
    def search_parts(self, query):
        query = query.lower()
        return [p for p in self.parts.values() 
                if query in p.name.lower() or query in p.part_id.lower() 
                or query in p.category.lower() or query in p.sku.lower()]
    
    def create_demo_data(self):
        # Demo customers
        demo_customers = [
            Customer("CUST-001", "ABC Manufacturing", "555-0101", "orders@abcmfg.com", "123 Business Park"),
            Customer("CUST-002", "XYZ Industries", "555-0102", "purchase@xyzind.com", "456 Corporate Dr"),
            Customer("CUST-003", "Tech Solutions", "555-0103", "procurement@techsol.com", "789 Innovation Way"),
        ]
        for cust in demo_customers:
            self.customers[cust.customer_id] = cust
        
        # Demo suppliers
        demo_suppliers = [
            Supplier("SUP-001", "ABC Motors Inc", "John Smith", "555-0201", "john@abcmotors.com", "123 Industrial Ave"),
            Supplier("SUP-002", "Precision Bearings", "Sarah Johnson", "555-0202", "sarah@precision.com", "456 Factory Rd"),
            Supplier("SUP-003", "Siemens", "Mike Brown", "555-0203", "mike@siemens.com", "789 Tech Park"),
        ]
        for sup in demo_suppliers:
            self.suppliers[sup.supplier_id] = sup
        
        # Demo parts
        demo_parts = [
            Part("MTR-001", "Electric Motor 5HP", "Mechanical", 12, 450.00, "ABC Motors Inc", "A-12", 5, 10, 320.00, "SKU-MTR-001"),
            Part("BRG-002", "Ball Bearing 6204", "Mechanical", 45, 12.50, "Precision Bearings", "B-08", 20, 50, 8.50, "SKU-BRG-002"),
            Part("CTL-003", "PLC Controller", "Electrical", 6, 1250.00, "Siemens", "D-01", 2, 5, 980.00, "SKU-CTL-003"),
            Part("SNS-004", "Temperature Sensor", "Electronic", 23, 45.75, "SensoTech", "E-15", 10, 20, 32.50, "SKU-SNS-004"),
            Part("VLV-005", "Solenoid Valve", "Pneumatic", 18, 78.30, "Pneumatics Plus", "F-22", 8, 15, 55.00, "SKU-VLV-005"),
            Part("BOL-006", "Hex Bolt M8x30", "Fasteners", 250, 0.85, "Fastener World", "H-01", 100, 200, 0.45, "SKU-BOL-006"),
        ]
        
        for part in demo_parts:
            part.total_sold = random.randint(0, 100)
            part.total_purchased = part.quantity + part.total_sold
            self.parts[part.part_id] = part
        
        # Demo transactions
        customers_list = list(self.customers.keys())
        for i in range(30):
            part_id = random.choice(list(self.parts.keys()))
            part = self.parts[part_id]
            quantity = random.randint(1, 5)
            days_ago = random.randint(0, 30)
            trans_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
            
            trans = Transaction(f"INV-{i:05d}", part_id, 'SALE', quantity,
                               part.selling_price, random.choice(customers_list), "Demo sale")
            trans.date = trans_date
            self.transactions.append(trans)
            part.total_sold += quantity
        
        self.save_all_data()
        print(f"Demo data created! {len(self.parts)} parts")


# ==================== INVOICE GENERATOR ====================

class InvoiceGenerator:
    @staticmethod
    def generate_invoice(transaction, part, customer):
        invoice_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Invoice {transaction.transaction_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f0f0; }}
                .invoice {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; }}
                .header {{ background: #2c3e50; color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #2c3e50; color: white; }}
                .total {{ text-align: right; font-size: 18px; font-weight: bold; margin-top: 20px; }}
                .footer {{ background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="invoice">
                <div class="header">
                    <h1>INVOICE</h1>
                    <p>{transaction.transaction_id}</p>
                </div>
                <div class="content">
                    <h3>Machine Parts Inventory Manager</h3>
                    <p>123 Industrial Area, Business District</p>
                    <hr>
                    <p><strong>Bill To:</strong><br>{customer.name if customer else transaction.customer_name}</p>
                    <table>
                        <tr><th>Item</th><th>Description</th><th>Qty</th><th>Price</th><th>Total</th></tr>
                        <tr>
                            <td>{part.part_id}</td>
                            <td>{part.name}</td>
                            <td>{transaction.quantity}</td>
                            <td>${transaction.price:.2f}</td>
                            <td>${transaction.quantity * transaction.price:.2f}</td>
                        </tr>
                    </table>
                    <div class="total">Total Amount: ${transaction.quantity * transaction.price * 1.18:.2f}</div>
                </div>
                <div class="footer"><p>Thank you for your business!</p></div>
            </div>
        </body>
        </html>
        """
        filename = f"invoice_{transaction.transaction_id}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(invoice_html)
        return filename


# ==================== LOGIN DIALOG ====================

class LoginDialog:
    def __init__(self, parent, manager):
        self.parent = parent
        self.manager = manager
        self.result = None
        
        self.dialog = Toplevel(parent)
        self.dialog.title("Login - Inventory Manager")
        self.dialog.geometry("450x500")
        self.dialog.configure(bg='#2c3e50')
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = Frame(self.dialog, bg='white', relief='flat')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        title = Label(main_frame, text="INVENTORY MANAGER", 
                     font=('Arial', 20, 'bold'), bg='white', fg='#2c3e50')
        title.pack(pady=30)
        
        subtitle = Label(main_frame, text="Machine Parts Inventory System", 
                        font=('Arial', 10), bg='white', fg='#7f8c8d')
        subtitle.pack(pady=5)
        
        login_frame = Frame(main_frame, bg='white')
        login_frame.pack(pady=30, padx=30, fill='both')
        
        Label(login_frame, text="Username", font=('Arial', 11, 'bold'), 
              bg='white', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        self.username_entry = Entry(login_frame, font=('Arial', 11), 
                                    width=30, relief='solid', bd=1)
        self.username_entry.pack(pady=(0, 15), fill='x')
        self.username_entry.insert(0, "admin")
        
        Label(login_frame, text="Password", font=('Arial', 11, 'bold'), 
              bg='white', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        self.password_entry = Entry(login_frame, font=('Arial', 11), 
                                    width=30, show="*", relief='solid', bd=1)
        self.password_entry.pack(pady=(0, 20), fill='x')
        self.password_entry.insert(0, "admin123")
        
        Button(login_frame, text="LOGIN", command=self.login,
               bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
               cursor='hand2', height=1, relief='flat').pack(fill='x', pady=10)
        
        info = Label(login_frame, text="Demo Credentials:\nUsername: admin\nPassword: admin123",
                    font=('Arial', 9), bg='white', fg='#95a5a6')
        info.pack(pady=15)
        
        self.password_entry.bind('<Return>', lambda e: self.login())
        self.username_entry.focus()
    
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Login Failed", "Please enter username and password!")
            return
        
        success, role = self.manager.authenticate(username, password)
        if success:
            self.result = role
            self.dialog.destroy()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password!")


# ==================== MAIN APPLICATION ====================

class InventoryApp:
    def __init__(self, root, manager, user_role):
        self.root = root
        self.manager = manager
        self.user_role = user_role
        self.categories = ['Mechanical', 'Electrical', 'Hydraulic', 'Pneumatic', 
                          'Electronic', 'Structural', 'Fasteners', 'Tools', 'Raw Materials', 'Other']
        
        self.setup_ui()
        self.refresh_all()
    
    def setup_ui(self):
        self.root.title("Machine Parts Inventory Manager")
        self.root.geometry("1400x850")
        self.root.configure(bg='#ecf0f1')
        
        # Header
        header = Frame(self.root, bg='#2c3e50', height=90)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title_frame = Frame(header, bg='#2c3e50')
        title_frame.pack(side='left', padx=30, pady=20)
        
        Label(title_frame, text="MACHINE PARTS INVENTORY MANAGER", 
              font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white').pack(side='left', padx=10)
        
        user_frame = Frame(header, bg='#2c3e50')
        user_frame.pack(side='right', padx=30)
        
        Label(user_frame, text=f"User: {self.manager.current_user.name}", 
              font=('Segoe UI', 10), bg='#2c3e50', fg='white').pack()
        Label(user_frame, text=f"Role: {self.user_role.upper()}", 
              font=('Segoe UI', 9), bg='#2c3e50', fg='#bdc3c7').pack()
        
        # Menu
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_command(label="Export to CSV", command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.about)
        
        # Toolbar
        toolbar = Frame(self.root, bg='#bdc3c7', height=45)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        quick_buttons = [
            ("Add Part", self.add_part_dialog, '#27ae60'),
            ("Make Sale", self.quick_sale, '#3498db'),
            ("Reports", self.show_reports, '#9b59b6'),
            ("Backup", self.backup_database, '#e67e22')
        ]
        
        for text, command, color in quick_buttons:
            btn = Button(toolbar, text=text, command=command, bg=color, fg='white',
                        font=('Segoe UI', 10), cursor='hand2', relief='flat', padx=15)
            btn.pack(side='left', padx=5, pady=8)
        
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_inventory_tab()
        self.create_sales_tab()
        self.create_transactions_tab()
        self.create_customers_tab()
        self.create_reports_tab()
        
        # Status bar
        self.status_bar = Label(self.root, text="System Ready", bd=1, relief='sunken', 
                                anchor='w', bg='#2c3e50', fg='white', font=('Segoe UI', 9))
        self.status_bar.pack(side='bottom', fill='x')
    
    def create_dashboard_tab(self):
        self.dashboard_tab = Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        
        cards_frame = Frame(self.dashboard_tab, bg='#ecf0f1')
        cards_frame.pack(pady=20, padx=20, fill='x')
        
        stats = self.manager.get_dashboard_stats()
        
        cards = [
            ("Total Parts", f"{stats['total_parts']}", "#3498db"),
            ("Inventory Value", f"${stats['total_value']:,.2f}", "#27ae60"),
            ("Low Stock", f"{stats['low_stock']}", "#e74c3c"),
            ("Today's Sales", f"${stats['today_sales']:,.2f}", "#f39c12"),
            ("Total Sales", f"${stats['total_sales']:,.2f}", "#9b59b6"),
            ("Customers", f"{stats['total_customers']}", "#1abc9c")
        ]
        
        for i, (title, value, color) in enumerate(cards):
            card = Frame(cards_frame, bg=color, relief='raised', bd=0)
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="nsew")
            Label(card, text=title, font=('Segoe UI', 11), bg=color, fg='white').pack(pady=10)
            Label(card, text=value, font=('Segoe UI', 18, 'bold'), bg=color, fg='white').pack(pady=10)
        
        for i in range(2):
            cards_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            cards_frame.grid_columnconfigure(i, weight=1)
        
        # Reorder alerts
        alert_frame = LabelFrame(self.dashboard_tab, text="REORDER ALERTS", 
                                 font=('Segoe UI', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50')
        alert_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.reorder_tree = ttk.Treeview(alert_frame, columns=('ID', 'Name', 'Stock', 'Min'), 
                                         show='headings', height=5)
        self.reorder_tree.heading('ID', text='Part ID')
        self.reorder_tree.heading('Name', text='Part Name')
        self.reorder_tree.heading('Stock', text='Current Stock')
        self.reorder_tree.heading('Min', text='Min Required')
        
        for col in ('ID', 'Name', 'Stock', 'Min'):
            self.reorder_tree.column(col, width=200 if col == 'Name' else 120)
        self.reorder_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Top selling
        top_frame = LabelFrame(self.dashboard_tab, text="TOP SELLING PARTS", 
                               font=('Segoe UI', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50')
        top_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.top_tree = ttk.Treeview(top_frame, columns=('Name', 'Sold', 'Revenue'), 
                                     show='headings', height=4)
        self.top_tree.heading('Name', text='Part Name')
        self.top_tree.heading('Sold', text='Total Sold')
        self.top_tree.heading('Revenue', text='Revenue')
        
        for col in ('Name', 'Sold', 'Revenue'):
            self.top_tree.column(col, width=250)
        self.top_tree.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_inventory_tab(self):
        self.inventory_tab = Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.inventory_tab, text="Inventory")
        
        control_frame = Frame(self.inventory_tab, bg='white', relief='raised', bd=1)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        search_frame = Frame(control_frame, bg='white')
        search_frame.pack(side='left', padx=15, pady=10)
        
        Label(search_frame, text="Search:", bg='white', font=('Segoe UI', 10)).pack(side='left', padx=5)
        self.search_entry = Entry(search_frame, width=35, font=('Segoe UI', 10), relief='solid', bd=1)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.search_inventory())
        
        Button(control_frame, text="Refresh", command=self.refresh_inventory,
               bg='#3498db', fg='white', font=('Segoe UI', 10), cursor='hand2',
               relief='flat', padx=15).pack(side='left', padx=5)
        
        Button(control_frame, text="Add Part", command=self.add_part_dialog,
               bg='#27ae60', fg='white', font=('Segoe UI', 10), cursor='hand2',
               relief='flat', padx=15).pack(side='right', padx=15)
        
        table_frame = Frame(self.inventory_tab)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scroll_y = Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        scroll_x = Scrollbar(table_frame, orient='horizontal')
        scroll_x.pack(side='bottom', fill='x')
        
        columns = ('ID', 'Name', 'Category', 'Stock', 'Price', 'Location', 'Status')
        self.inventory_tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                           yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set, height=20)
        
        headings = ['Part ID', 'Part Name', 'Category', 'Stock', 'Price', 'Location', 'Status']
        for col, heading in zip(columns, headings):
            self.inventory_tree.heading(col, text=heading)
            self.inventory_tree.column(col, width=150)
        self.inventory_tree.column('Name', width=250)
        self.inventory_tree.pack(fill='both', expand=True)
        
        scroll_y.config(command=self.inventory_tree.yview)
        scroll_x.config(command=self.inventory_tree.xview)
        
        self.context_menu = Menu(self.inventory_tree, tearoff=0)
        self.context_menu.add_command(label="Sell Part", command=self.sell_from_inventory)
        self.context_menu.add_command(label="Restock Part", command=self.restock_from_inventory)
        self.context_menu.add_command(label="Edit Part", command=self.edit_part_dialog)
        self.context_menu.add_command(label="Delete Part", command=self.delete_part)
        self.inventory_tree.bind("<Button-3>", self.show_context_menu)
        
        self.refresh_inventory()
    
    def create_sales_tab(self):
        self.sales_tab = Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.sales_tab, text="Sales")
        
        left_panel = Frame(self.sales_tab, bg='white', relief='raised', bd=1)
        left_panel.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        Label(left_panel, text="PROCESS SALE", font=('Segoe UI', 16, 'bold'),
              bg='white', fg='#2c3e50').pack(pady=20)
        
        Label(left_panel, text="Select Customer:", bg='white', font=('Segoe UI', 10)).pack(pady=5)
        self.customer_combo = ttk.Combobox(left_panel, width=45, font=('Segoe UI', 10))
        self.customer_combo.pack(pady=5)
        self.refresh_customers()
        
        Label(left_panel, text="Search Part:", bg='white', font=('Segoe UI', 10)).pack(pady=5)
        self.part_search = Entry(left_panel, width=45, font=('Segoe UI', 10), relief='solid', bd=1)
        self.part_search.pack(pady=5)
        self.part_search.bind('<KeyRelease>', lambda e: self.search_parts_for_sale())
        
        self.part_listbox = Listbox(left_panel, height=8, width=55, font=('Segoe UI', 10))
        self.part_listbox.pack(pady=5)
        self.part_listbox.bind('<<ListboxSelect>>', self.on_part_select)
        
        self.selected_part_label = Label(left_panel, text="Selected: None",
                                         bg='white', fg='#27ae60', font=('Segoe UI', 10))
        self.selected_part_label.pack(pady=5)
        
        Label(left_panel, text="Quantity:", bg='white', font=('Segoe UI', 10)).pack(pady=5)
        self.sale_quantity = Entry(left_panel, width=20, font=('Segoe UI', 10), relief='solid', bd=1)
        self.sale_quantity.pack(pady=5)
        
        Label(left_panel, text="Price Override (optional):", bg='white', font=('Segoe UI', 10)).pack(pady=5)
        self.price_override = Entry(left_panel, width=20, font=('Segoe UI', 10), relief='solid', bd=1)
        self.price_override.pack(pady=5)
        
        Button(left_panel, text="PROCESS SALE & GENERATE INVOICE", 
               command=self.process_sale,
               bg='#27ae60', fg='white', font=('Segoe UI', 12, 'bold'),
               cursor='hand2', height=2, relief='flat').pack(pady=20, padx=20, fill='x')
        
        right_panel = Frame(self.sales_tab, bg='white', relief='raised', bd=1)
        right_panel.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        Label(right_panel, text="RECENT SALES", font=('Segoe UI', 14, 'bold'),
              bg='white', fg='#2c3e50').pack(pady=10)
        
        self.sales_tree = ttk.Treeview(right_panel, columns=('Date', 'Customer', 'Part', 'Qty', 'Total'),
                                       show='headings', height=25)
        self.sales_tree.heading('Date', text='Date')
        self.sales_tree.heading('Customer', text='Customer')
        self.sales_tree.heading('Part', text='Part')
        self.sales_tree.heading('Qty', text='Qty')
        self.sales_tree.heading('Total', text='Total')
        
        for col in ('Date', 'Customer', 'Part', 'Qty', 'Total'):
            self.sales_tree.column(col, width=130)
        self.sales_tree.column('Part', width=180)
        self.sales_tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.sales_tree.bind('<Double-Button-1>', self.view_invoice)
        
        self.refresh_sales_history()
    
    def create_transactions_tab(self):
        self.transactions_tab = Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.transactions_tab, text="Transactions")
        
        filter_frame = Frame(self.transactions_tab, bg='white', relief='raised', bd=1)
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        Label(filter_frame, text="Filter:", bg='white', font=('Segoe UI', 10)).pack(side='left', padx=10)
        self.trans_filter = ttk.Combobox(filter_frame, values=['All', 'SALE', 'PURCHASE'], width=15)
        self.trans_filter.set('All')
        self.trans_filter.pack(side='left', padx=5)
        self.trans_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_transactions())
        
        Button(filter_frame, text="Refresh", command=self.refresh_transactions,
               bg='#3498db', fg='white', font=('Segoe UI', 10), cursor='hand2',
               relief='flat', padx=15).pack(side='left', padx=10)
        
        table_frame = Frame(self.transactions_tab)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scroll_y = Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        
        columns = ('Date', 'ID', 'Type', 'Part', 'Qty', 'Price', 'Total', 'Customer')
        self.trans_tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                       yscrollcommand=scroll_y.set, height=20)
        for col in columns:
            self.trans_tree.heading(col, text=col)
            self.trans_tree.column(col, width=130)
        self.trans_tree.pack(fill='both', expand=True)
        scroll_y.config(command=self.trans_tree.yview)
        
        self.refresh_transactions()
    
    def create_customers_tab(self):
        self.customers_tab = Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.customers_tab, text="Customers")
        
        control_frame = Frame(self.customers_tab, bg='white', relief='raised', bd=1)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        Button(control_frame, text="Add Customer", command=self.add_customer_dialog,
               bg='#27ae60', fg='white', font=('Segoe UI', 10), cursor='hand2',
               relief='flat', padx=15).pack(side='left', padx=10, pady=10)
        
        Button(control_frame, text="Refresh", command=self.refresh_customers_table,
               bg='#3498db', fg='white', font=('Segoe UI', 10), cursor='hand2',
               relief='flat', padx=15).pack(side='left', padx=5, pady=10)
        
        table_frame = Frame(self.customers_tab)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scroll_y = Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        
        columns = ('ID', 'Name', 'Phone', 'Email', 'Purchases', 'Spent')
        self.customers_tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                           yscrollcommand=scroll_y.set, height=20)
        for col in columns:
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=150)
        self.customers_tree.pack(fill='both', expand=True)
        scroll_y.config(command=self.customers_tree.yview)
        
        self.refresh_customers_table()
    
    def create_reports_tab(self):
        self.reports_tab = Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(self.reports_tab, text="Reports")
        
        control_frame = Frame(self.reports_tab, bg='white', relief='raised', bd=1)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        reports = [
            ("Full Report", self.full_report),
            ("Low Stock Report", self.low_stock_report),
            ("Sales Summary", self.sales_summary)
        ]
        
        for text, command in reports:
            Button(control_frame, text=text, command=command,
                   bg='#3498db', fg='white', font=('Segoe UI', 10), cursor='hand2',
                   relief='flat', padx=15).pack(side='left', padx=5, pady=10)
        
        self.report_text = Text(self.reports_tab, wrap='word', font=('Courier', 10),
                                bg='white', fg='#2c3e50', insertbackground='#2c3e50')
        self.report_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = Scrollbar(self.report_text)
        scrollbar.pack(side='right', fill='y')
        self.report_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.report_text.yview)
    
    # ==================== Helper Methods ====================
    
    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_inventory()
        self.refresh_transactions()
        self.refresh_sales_history()
        self.refresh_customers_table()
    
    def refresh_dashboard(self):
        for item in self.reorder_tree.get_children():
            self.reorder_tree.delete(item)
        for part in self.manager.get_reorder_list():
            self.reorder_tree.insert('', 'end', values=(part.part_id, part.name, part.quantity, part.min_quantity))
        
        for item in self.top_tree.get_children():
            self.top_tree.delete(item)
        for part in self.manager.get_top_selling_parts():
            revenue = part.total_sold * part.selling_price
            self.top_tree.insert('', 'end', values=(part.name, part.total_sold, f"${revenue:,.2f}"))
    
    def refresh_inventory(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        for part in self.manager.parts.values():
            status = "LOW" if part.needs_reorder else "OK"
            self.inventory_tree.insert('', 'end', values=(part.part_id, part.name, part.category, part.quantity,
                                                          f"${part.selling_price:.2f}", part.location, status))
    
    def search_inventory(self):
        query = self.search_entry.get().lower()
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        for part in self.manager.parts.values():
            if query and query not in part.name.lower() and query not in part.part_id.lower():
                continue
            status = "LOW" if part.needs_reorder else "OK"
            self.inventory_tree.insert('', 'end', values=(part.part_id, part.name, part.category, part.quantity,
                                                          f"${part.selling_price:.2f}", part.location, status))
    
    def refresh_transactions(self):
        for item in self.trans_tree.get_children():
            self.trans_tree.delete(item)
        filter_type = self.trans_filter.get()
        for trans in self.manager.transactions[:200]:
            if filter_type != 'All' and trans.transaction_type != filter_type:
                continue
            part = self.manager.parts.get(trans.part_id, None)
            part_name = part.name if part else trans.part_id
            total = trans.quantity * trans.price
            self.trans_tree.insert('', 0, values=(
                trans.date[:16], trans.transaction_id, trans.transaction_type,
                part_name[:25], trans.quantity, f"${trans.price:.2f}",
                f"${total:.2f}", trans.customer_name[:20]
            ))
    
    def refresh_sales_history(self):
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)
        sales = [t for t in self.manager.transactions if t.transaction_type == 'SALE'][:30]
        for sale in sales:
            part = self.manager.parts.get(sale.part_id, None)
            part_name = part.name if part else sale.part_id
            total = sale.quantity * sale.price
            self.sales_tree.insert('', 0, values=(
                sale.date[:16], sale.customer_name[:20], part_name[:25],
                sale.quantity, f"${total:,.2f}"
            ))
    
    def refresh_customers(self):
        customers = [f"{c.customer_id} - {c.name}" for c in self.manager.customers.values()]
        self.customer_combo['values'] = customers
    
    def refresh_customers_table(self):
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        for customer in self.manager.customers.values():
            self.customers_tree.insert('', 'end', values=(
                customer.customer_id, customer.name, customer.phone,
                customer.email, customer.total_purchases, f"${customer.total_spent:,.2f}"
            ))
    
    def search_parts_for_sale(self):
        query = self.part_search.get()
        self.part_listbox.delete(0, 'end')
        results = self.manager.search_parts(query) if query else list(self.manager.parts.values())[:20]
        for part in results:
            self.part_listbox.insert('end', f"{part.part_id} - {part.name} (Stock: {part.quantity}) | ${part.selling_price:.2f}")
            self.part_listbox.part_data = results
    
    def on_part_select(self, event):
        selection = self.part_listbox.curselection()
        if selection:
            index = selection[0]
            part = self.part_listbox.part_data[index]
            self.selected_part = part
            self.selected_part_label.config(text=f"Selected: {part.name} (${part.selling_price:.2f} each) | Stock: {part.quantity}")
            self.selected_part_id = part.part_id
    
    def process_sale(self):
        if not hasattr(self, 'selected_part_id'):
            messagebox.showwarning("Warning", "Please select a part first!")
            return
        
        customer_text = self.customer_combo.get()
        customer_id = customer_text.split(' - ')[0] if ' - ' in customer_text else ""
        
        try:
            quantity = int(self.sale_quantity.get())
            if quantity <= 0:
                messagebox.showerror("Error", "Quantity must be positive!")
                return
            
            price_override = float(self.price_override.get()) if self.price_override.get() else None
            
            success, transaction, message = self.manager.sell_part(
                self.selected_part_id, quantity, customer_id, price_override
            )
            
            if success:
                part = self.manager.parts.get(self.selected_part_id)
                customer = self.manager.customers.get(customer_id) if customer_id else None
                invoice_file = InvoiceGenerator.generate_invoice(transaction, part, customer)
                messagebox.showinfo("Success", f"{message}\n\nInvoice saved as: {invoice_file}")
                self.sale_quantity.delete(0, 'end')
                self.price_override.delete(0, 'end')
                self.refresh_all()
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity!")
    
    def view_invoice(self, event):
        selection = self.sales_tree.selection()
        if not selection:
            return
        values = self.sales_tree.item(selection[0])['values']
        invoice_id = values[1]
        invoice_file = f"invoice_{invoice_id}.html"
        if os.path.exists(invoice_file):
            webbrowser.open(invoice_file)
        else:
            messagebox.showwarning("Not Found", "Invoice file not found!")
    
    def add_part_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add New Part")
        dialog.geometry("550x600")
        dialog.configure(bg='white')
        
        fields = {}
        labels = [
            ('Part ID:', 'part_id'), ('Part Name:', 'name'),
            ('Category:', 'category'), ('Quantity:', 'quantity'),
            ('Selling Price:', 'price'), ('Cost Price:', 'cost'),
            ('Supplier:', 'supplier'), ('Location:', 'location'),
            ('Min Stock:', 'min_qty'), ('SKU:', 'sku')
        ]
        
        row = 0
        for label, key in labels:
            Label(dialog, text=label, bg='white', font=('Segoe UI', 10)).grid(row=row, column=0, sticky='w', padx=20, pady=8)
            entry = Entry(dialog, width=35, font=('Segoe UI', 10), relief='solid', bd=1)
            entry.grid(row=row, column=1, padx=20, pady=8)
            fields[key] = entry
            
            if key == 'category':
                entry.insert(0, self.categories[0])
            elif key == 'min_qty':
                entry.insert(0, '5')
            row += 1
        
        def save():
            try:
                part_id = fields['part_id'].get().strip()
                if not part_id:
                    part_id = f"PART-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                part = Part(
                    part_id,
                    fields['name'].get().strip(),
                    fields['category'].get(),
                    int(fields['quantity'].get()),
                    float(fields['price'].get()),
                    fields['supplier'].get().strip() or "Unknown",
                    fields['location'].get().strip(),
                    int(fields['min_qty'].get()) if fields['min_qty'].get() else 5,
                    10,
                    float(fields['cost'].get()) if fields['cost'].get() else 0,
                    fields['sku'].get().strip()
                )
                
                success, message = self.manager.add_part(part)
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
        
        Button(dialog, text="Save Part", command=save,
               bg='#27ae60', fg='white', font=('Segoe UI', 11, 'bold'),
               cursor='hand2', relief='flat', padx=20, pady=8).grid(row=row, column=0, columnspan=2, pady=20)
    
    def edit_part_dialog(self):
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a part to edit!")
            return
        
        values = self.inventory_tree.item(selected[0])['values']
        part_id = values[0]
        part = self.manager.parts.get(part_id)
        
        if not part:
            return
        
        dialog = Toplevel(self.root)
        dialog.title(f"Edit Part - {part.name}")
        dialog.geometry("550x600")
        dialog.configure(bg='white')
        
        fields = {}
        labels = [
            ('Part ID:', 'part_id'), ('Part Name:', 'name'),
            ('Category:', 'category'), ('Quantity:', 'quantity'),
            ('Selling Price:', 'price'), ('Cost Price:', 'cost'),
            ('Supplier:', 'supplier'), ('Location:', 'location'),
            ('Min Stock:', 'min_qty'), ('SKU:', 'sku')
        ]
        
        row = 0
        for label, key in labels:
            Label(dialog, text=label, bg='white', font=('Segoe UI', 10)).grid(row=row, column=0, sticky='w', padx=20, pady=8)
            entry = Entry(dialog, width=35, font=('Segoe UI', 10), relief='solid', bd=1)
            entry.grid(row=row, column=1, padx=20, pady=8)
            
            if key == 'part_id':
                entry.insert(0, part.part_id)
                entry.config(state='readonly')
            elif key == 'name':
                entry.insert(0, part.name)
            elif key == 'category':
                entry.insert(0, part.category)
            elif key == 'quantity':
                entry.insert(0, part.quantity)
            elif key == 'price':
                entry.insert(0, part.selling_price)
            elif key == 'cost':
                entry.insert(0, part.cost_price)
            elif key == 'supplier':
                entry.insert(0, part.supplier)
            elif key == 'location':
                entry.insert(0, part.location)
            elif key == 'min_qty':
                entry.insert(0, part.min_quantity)
            elif key == 'sku':
                entry.insert(0, part.sku)
            
            fields[key] = entry
            row += 1
        
        def update():
            try:
                updates = {
                    'name': fields['name'].get().strip(),
                    'category': fields['category'].get(),
                    'quantity': int(fields['quantity'].get()),
                    'selling_price': float(fields['price'].get()),
                    'cost_price': float(fields['cost'].get()) if fields['cost'].get() else 0,
                    'supplier': fields['supplier'].get().strip(),
                    'location': fields['location'].get().strip(),
                    'min_quantity': int(fields['min_qty'].get()),
                    'sku': fields['sku'].get().strip()
                }
                
                success, message = self.manager.update_part(part.part_id, **updates)
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {str(e)}")
        
        Button(dialog, text="Update Part", command=update,
               bg='#3498db', fg='white', font=('Segoe UI', 11, 'bold'),
               cursor='hand2', relief='flat', padx=20, pady=8).grid(row=row, column=0, columnspan=2, pady=20)
    
    def delete_part(self):
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a part to delete!")
            return
        
        values = self.inventory_tree.item(selected[0])['values']
        part_id = values[0]
        part_name = values[1]
        
        if messagebox.askyesno("Confirm Delete", f"Delete '{part_name}'? This cannot be undone!"):
            success, message = self.manager.delete_part(part_id)
            if success:
                messagebox.showinfo("Success", message)
                self.refresh_all()
            else:
                messagebox.showerror("Error", message)
    
    def sell_from_inventory(self):
        selected = self.inventory_tree.selection()
        if not selected:
            return
        
        values = self.inventory_tree.item(selected[0])['values']
        part_id = values[0]
        part_name = values[1]
        current_stock = values[3]
        
        dialog = Toplevel(self.root)
        dialog.title(f"Sell - {part_name}")
        dialog.geometry("400x350")
        dialog.configure(bg='white')
        
        Label(dialog, text=f"Selling: {part_name}", font=('Segoe UI', 14, 'bold'),
              bg='white', fg='#2c3e50').pack(pady=15)
        Label(dialog, text=f"Current Stock: {current_stock}", bg='white').pack(pady=5)
        
        Label(dialog, text="Quantity:", bg='white').pack(pady=5)
        quantity_entry = Entry(dialog, width=20)
        quantity_entry.pack(pady=5)
        
        Label(dialog, text="Customer:", bg='white').pack(pady=5)
        customer_combo = ttk.Combobox(dialog, width=30)
        customers = [f"{c.customer_id} - {c.name}" for c in self.manager.customers.values()]
        customer_combo['values'] = customers
        customer_combo.pack(pady=5)
        
        def process():
            try:
                quantity = int(quantity_entry.get())
                if quantity <= 0:
                    messagebox.showerror("Error", "Quantity must be positive!")
                    return
                
                customer_text = customer_combo.get()
                customer_id = customer_text.split(' - ')[0] if ' - ' in customer_text else ""
                
                success, transaction, message = self.manager.sell_part(part_id, quantity, customer_id)
                if success:
                    customer = self.manager.customers.get(customer_id) if customer_id else None
                    invoice_file = InvoiceGenerator.generate_invoice(transaction, self.manager.parts[part_id], customer)
                    messagebox.showinfo("Success", f"{message}\n\nInvoice: {invoice_file}")
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity!")
        
        Button(dialog, text="Process Sale", command=process,
               bg='#27ae60', fg='white', font=('Segoe UI', 11, 'bold'),
               cursor='hand2', relief='flat', padx=20, pady=8).pack(pady=20)
    
    def restock_from_inventory(self):
        selected = self.inventory_tree.selection()
        if not selected:
            return
        
        values = self.inventory_tree.item(selected[0])['values']
        part_id = values[0]
        part_name = values[1]
        
        dialog = Toplevel(self.root)
        dialog.title(f"Restock - {part_name}")
        dialog.geometry("400x300")
        dialog.configure(bg='white')
        
        Label(dialog, text=f"Restocking: {part_name}", font=('Segoe UI', 14, 'bold'),
              bg='white', fg='#2c3e50').pack(pady=15)
        
        Label(dialog, text="Quantity to Add:", bg='white').pack(pady=5)
        quantity_entry = Entry(dialog, width=20)
        quantity_entry.pack(pady=5)
        
        Label(dialog, text="Purchase Price per Unit:", bg='white').pack(pady=5)
        price_entry = Entry(dialog, width=20)
        price_entry.pack(pady=5)
        
        def process():
            try:
                quantity = int(quantity_entry.get())
                price = float(price_entry.get())
                
                if quantity <= 0:
                    messagebox.showerror("Error", "Quantity must be positive!")
                    return
                
                success, message = self.manager.purchase_part(part_id, quantity, price)
                if success:
                    messagebox.showinfo("Success", message)
                    dialog.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
            except ValueError:
                messagebox.showerror("Error", "Invalid input!")
        
        Button(dialog, text="Process Restock", command=process,
               bg='#3498db', fg='white', font=('Segoe UI', 11, 'bold'),
               cursor='hand2', relief='flat', padx=20, pady=8).pack(pady=20)
    
    def add_customer_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add Customer")
        dialog.geometry("500x450")
        dialog.configure(bg='white')
        
        fields = {}
        labels = [
            ('Customer ID:', 'cust_id'), ('Name:', 'name'),
            ('Phone:', 'phone'), ('Email:', 'email'),
            ('Address:', 'address')
        ]
        
        row = 0
        for label, key in labels:
            Label(dialog, text=label, bg='white', font=('Segoe UI', 10)).grid(row=row, column=0, sticky='w', padx=20, pady=8)
            entry = Entry(dialog, width=35, font=('Segoe UI', 10), relief='solid', bd=1)
            entry.grid(row=row, column=1, padx=20, pady=8)
            fields[key] = entry
            row += 1
        
        def save():
            cust_id = fields['cust_id'].get().strip()
            if not cust_id:
                cust_id = f"CUST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            customer = Customer(
                cust_id,
                fields['name'].get().strip(),
                fields['phone'].get().strip(),
                fields['email'].get().strip(),
                fields['address'].get().strip()
            )
            
            success, message = self.manager.add_customer(customer)
            if success:
                messagebox.showinfo("Success", message)
                dialog.destroy()
                self.refresh_all()
            else:
                messagebox.showerror("Error", message)
        
        Button(dialog, text="Save Customer", command=save,
               bg='#27ae60', fg='white', font=('Segoe UI', 11, 'bold'),
               cursor='hand2', relief='flat', padx=20, pady=8).grid(row=row, column=0, columnspan=2, pady=20)
    
    def full_report(self):
        report = []
        report.append("="*80)
        report.append("INVENTORY MANAGEMENT REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*80)
        
        stats = self.manager.get_dashboard_stats()
        report.append("\nEXECUTIVE SUMMARY")
        report.append("-"*40)
        report.append(f"Total Parts:              {stats['total_parts']}")
        report.append(f"Inventory Value:          ${stats['total_value']:,.2f}")
        report.append(f"Total Sales:              ${stats['total_sales']:,.2f}")
        report.append(f"Low Stock Items:          {stats['low_stock']}")
        report.append(f"Today's Sales:            ${stats['today_sales']:,.2f}")
        report.append(f"Total Customers:          {stats['total_customers']}")
        
        report.append("\nLOW STOCK ITEMS")
        report.append("-"*40)
        for part in self.manager.get_reorder_list():
            report.append(f"• {part.name}: {part.quantity} left (Min: {part.min_quantity})")
        
        report.append("\nTOP SELLING PARTS")
        report.append("-"*40)
        for part in self.manager.get_top_selling_parts(10):
            revenue = part.total_sold * part.selling_price
            report.append(f"• {part.name}: {part.total_sold} sold - ${revenue:,.2f} revenue")
        
        self.report_text.delete(1.0, 'end')
        self.report_text.insert(1.0, "\n".join(report))
    
    def low_stock_report(self):
        report = []
        report.append("LOW STOCK REPORT")
        report.append("="*50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        low_stock = self.manager.get_reorder_list()
        if low_stock:
            for part in low_stock:
                report.append(f"\nPart: {part.name}")
                report.append(f"  ID: {part.part_id}")
                report.append(f"  Current Stock: {part.quantity}")
                report.append(f"  Minimum Required: {part.min_quantity}")
                report.append(f"  Supplier: {part.supplier}")
        else:
            report.append("No low stock items found!")
        
        self.report_text.delete(1.0, 'end')
        self.report_text.insert(1.0, "\n".join(report))
    
    def sales_summary(self):
        report = []
        report.append("SALES SUMMARY REPORT")
        report.append("="*50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        monthly_sales = defaultdict(float)
        for trans in self.manager.transactions:
            if trans.transaction_type == 'SALE':
                month = trans.date[:7]
                monthly_sales[month] += trans.quantity * trans.price
        
        for month, amount in sorted(monthly_sales.items(), reverse=True):
            report.append(f"{month}: ${amount:,.2f}")
        
        self.report_text.delete(1.0, 'end')
        self.report_text.insert(1.0, "\n".join(report))
    
    def show_context_menu(self, event):
        item = self.inventory_tree.identify_row(event.y)
        if item:
            self.inventory_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def quick_sale(self):
        self.notebook.select(2)
    
    def show_reports(self):
        self.notebook.select(5)
    
    def backup_database(self):
        backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        if os.path.exists("data"):
            for file in os.listdir("data"):
                if file.endswith('.json'):
                    shutil.copy(os.path.join("data", file), os.path.join(backup_dir, file))
        
        messagebox.showinfo("Backup Complete", f"Backup saved to: {backup_dir}")
        self.status_bar.config(text=f"Backup created: {backup_dir}")
    
    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Part ID', 'Name', 'Category', 'Quantity', 'Price', 'Supplier', 'Location'])
                for part in self.manager.parts.values():
                    writer.writerow([part.part_id, part.name, part.category, part.quantity, 
                                    part.selling_price, part.supplier, part.location])
            messagebox.showinfo("Success", f"Exported to {filename}")
    
    def about(self):
        messagebox.showinfo("About", "Machine Parts Inventory Manager\nVersion 2.0\n\nFeatures:\n• Inventory Management\n• Sales Tracking\n• Invoice Generation\n• Customer Management\n• Reports")


# ==================== MAIN FUNCTION ====================

def main():
    root = Tk()
    manager = InventoryManager()
    
    login_dialog = LoginDialog(root, manager)
    root.wait_window(login_dialog.dialog)
    
    if login_dialog.result:
        app = InventoryApp(root, manager, login_dialog.result)
        
        root.update_idletasks()
        width = 1400
        height = 850
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        root.mainloop()
    else:
        root.destroy()


if __name__ == "__main__":
    main()
