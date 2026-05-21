# Machine Parts Inventory Manager

A comprehensive Python desktop application for managing machine part inventory, sales, customers, and generating invoices.

## 🚀 Features

- **Inventory Tracking** - Manage stock levels and storage locations
- **Low Stock Alerts** - Automated warnings when parts need reordering
- **Sales Management** - Process transactions and track revenue
- **Invoicing** - Generate professional HTML invoices automatically
- **Secure Login** - Encrypted password protection for admin and staff
- **Customer Management** - Track purchase history per customer
- **Supplier Management** - Maintain supplier information
- **Reporting System** - Generate sales and inventory reports
- **Data Backup** - One-click database backup functionality
- **CSV Export** - Export inventory data to CSV format

## 🛠️ Built With

- **Python** - Core logic and backend
- **Tkinter** - GUI framework
- **JSON** - Local data storage
- **Hashlib** - Password encryption
- **Webbrowser** - Invoice display

## 📦 Installation

### Prerequisites
- Python 3.6 or higher installed on your system

### Steps

1. Clone the repository or download the file:
```bash
git clone https://github.com/yourusername/machine-parts-inventory.git
cd machine-parts-inventory
Run the application:

bash
python inventory_manager.py
Note: No additional libraries need to be installed as all dependencies are part of Python's standard library.

🔐 Default Login
Field	Value
Username	admin
Password	admin123
Role	Administrator
📁 Project Structure
text
machine-parts-inventory/
├── inventory_manager.py    # Main application file
├── data/                   # Data storage (auto-created)
│   ├── inventory.json      # Parts inventory
│   ├── transactions.json   # Sales/purchase records
│   ├── users.json         # User accounts
│   ├── customers.json     # Customer data
│   └── suppliers.json     # Supplier data
├── backup_*/              # Automatic backups
└── invoice_*.html         # Generated invoices
🎯 How to Use
Adding a New Part
Go to Inventory tab

Click Add Part button

Enter part details (ID, name, quantity, price, etc.)

Click Save Part

Processing a Sale
Go to Sales tab

Search and select a part from the list

Enter quantity and select customer

Click Process Sale & Generate Invoice

Invoice opens automatically in your browser

Checking Low Stock
View Dashboard tab for low stock alerts

Parts with stock below minimum are highlighted in red

Creating Backup
Click File menu

Select Backup Database

A timestamped backup folder is created

Exporting Data
Click File menu

Select Export to CSV

Choose save location

📊 Database Schema
Part (Inventory)
Field	Type	Description
part_id	string	Primary key
name	string	Part name
category	string	Mechanical, Electrical, etc.
quantity	integer	Current stock
selling_price	float	Sale price
cost_price	float	Purchase cost
supplier	string	Supplier name
location	string	Storage location
Transaction
Field	Type	Description
transaction_id	string	Primary key (INV-xxx or PO-xxx)
part_id	string	Foreign key to Part
type	string	SALE or PURCHASE
quantity	integer	Units transacted
price	float	Unit price
📈 Reports Available
Report	Description
Full Report	Complete inventory analysis
Low Stock Report	Items needing reorder
Sales Summary	Monthly sales breakdown
Top Selling	Best performing parts
💻 System Requirements
Component	Requirement
OS	Windows 7+, macOS, Linux
Python	3.6 or higher
RAM	256 MB minimum
Disk Space	50 MB
🚦 Error Handling
The application handles:

Invalid login credentials

Insufficient stock during sales

Duplicate part/customer IDs

Invalid numeric inputs

Missing data files (auto-creates on startup)

File I/O errors

📝 Demo Data
On first run, the system automatically populates:

6 sample parts

3 customer records

3 supplier records

30 sample transactions

🤝 Contributing
Fork the repository

Create a feature branch (git checkout -b feature/amazing)

Commit changes (git commit -m 'Add amazing feature')

Push to branch (git push origin feature/amazing)

Open a Pull Request

📄 License
This project is for educational purposes.

👨‍💻 Author
Developed as a Mini Project

Quick Start Commands
bash
# Run the application
python inventory_manager.py

# Create a backup (from within app)
# File → Backup Database

# Export data (from within app)  
# File → Export to CSV
text

This README is:
- **Git-friendly** - Uses proper markdown formatting
- **Copy-paste ready** - Just save as `README.md`
- **Clear structure** - Headings, tables, and code blocks
- **Beginner-friendly** - Explains everything step by step
- **Professional** - Includes all standard GitHub sections
