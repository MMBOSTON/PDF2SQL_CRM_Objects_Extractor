from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, Date, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import text
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import logging

# Setup logging to write to both terminal and file
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger()

# Create file handler which logs even debug messages
fh = logging.FileHandler('crud_ops_report.log')
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter(log_format))

# Add the handlers to the logger
logger.addHandler(fh)


Base = declarative_base()

class CrmAccount(Base):
    __tablename__ = 'crm_accounts'

    #id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    #id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(Integer, primary_key=True)
    account_name = Column(String(100), nullable=False)
    account_type = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    parent_account = Column(Integer, nullable=False)
    phone = Column(String(50), nullable=False)
    website = Column(String(100), nullable=False)
    industry = Column(Integer, nullable=False)
    employees = Column(Integer, nullable=False)
    billing_address = Column(Text, nullable=False)
    billing_street = Column(String(50), nullable=False)
    billing_city = Column(String(50), nullable=False)
    billing_state = Column(String(50), nullable=False)
    billing_post_code = Column(String(20), nullable=False)
    billing_country = Column(Integer, nullable=False)
    shipping_address = Column(Text, nullable=False)
    shipping_street = Column(String(50), nullable=False)
    shipping_city = Column(String(50), nullable=False)
    shipping_state = Column(String(50), nullable=False)
    shipping_post_code = Column(String(20), nullable=False)
    shipping_country = Column(Integer, nullable=False)
    assign_to = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, nullable=False)
    deleted_at = Column(DateTime)
    deleted_by = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=False)
    valid = Column(Boolean, nullable=False)

# Create engine and session
engine = create_engine('sqlite:///crm_objects.db', echo=True)
Session = sessionmaker(bind=engine)

# Create tables in the database
Base.metadata.create_all(engine)

def get_next_id(session):
    max_id = session.query(func.max(CrmAccount.id)).scalar()
    return (max_id or 0) + 1

# CRUD operations
def create_account(session, **kwargs):
    next_id = get_next_id(session)
    kwargs['id'] = next_id
    new_account = CrmAccount(**kwargs)
    session.add(new_account)
    session.commit()
    return new_account

def read_account(session, account_id):
    return session.query(CrmAccount).filter_by(id=account_id).first()

def update_account(session, account_id, **kwargs):
    account = session.query(CrmAccount).filter_by(id=account_id).first()
    if account:
        for key, value in kwargs.items():
            setattr(account, key, value)
        session.commit()
    return account

def delete_account(session, account_id):
    account = session.query(CrmAccount).filter_by(id=account_id).first()
    if account:
        session.delete(account)
        session.commit()
    return account

# Schema modification and migration
def column_exists(engine, table_name, column_name):
    query = text(f"PRAGMA table_info({table_name})")
    with engine.connect() as conn:
        result = conn.execute(query)
        keys = list(result.keys())
        name_index = keys.index('name')
        columns = [row[name_index] for row in result]
        return column_name in columns

def add_column(engine, table_name, column):
    column_name = column.name
    column_type = column.type.compile(engine.dialect)
    if not column_exists(engine, table_name, column_name):
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
            conn.commit()
    else:
        print(f"Column '{column_name}' already exists in '{table_name}'.")

def migrate_database(engine, Base):
    Base.metadata.create_all(engine)

# Additional functions
def get_all_accounts(session):
    return session.query(CrmAccount).all()

def get_accounts_by_type(session, account_type):
    return session.query(CrmAccount).filter_by(account_type=account_type).all()

def get_account_by_name(session, account_name):
    return session.query(CrmAccount).filter_by(account_name=account_name).first()

def count_accounts(session):
    return session.query(CrmAccount).count()

def get_accounts_by_industry(session, industry):
    return session.query(CrmAccount).filter_by(industry=industry).all()

def get_accounts_by_city(session, city):
    return session.query(CrmAccount).filter((CrmAccount.billing_city == city) | (CrmAccount.shipping_city == city)).all()

def get_recent_accounts(session, days=30):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return session.query(CrmAccount).filter(CrmAccount.created_at >= cutoff_date).all()

def deactivate_account(session, account_id):
    account = session.query(CrmAccount).filter_by(id=account_id).first()
    if account:
        account.valid = False
        session.commit()
    return account

def activate_account(session, account_id):
    account = session.query(CrmAccount).filter_by(id=account_id).first()
    if account:
        account.valid = True
        session.commit()
    return account

def get_inactive_accounts(session):
    return session.query(CrmAccount).filter_by(valid=False).all()

# Test function to create sample accounts
def create_test_accounts(session):
    test_accounts = [
        {
            "account_name": "Test Account 1",
            "account_type": 1,
            "description": "Test description 1",
            "parent_account": 0,
            "phone": "123-456-7890",
            "website": "www.test1.com",
            "industry": 1,
            "employees": 100,
            "billing_address": "123 Test St",
            "billing_street": "Test St",
            "billing_city": "Test City",
            "billing_state": "TS",
            "billing_post_code": "12345",
            "billing_country": 1,
            "shipping_address": "123 Test St",
            "shipping_street": "Test St",
            "shipping_city": "Test City",
            "shipping_state": "TS",
            "shipping_post_code": "12345",
            "shipping_country": 1,
            "assign_to": 1,
            "created_by": 1,
            "updated_by": 1,
            "deleted_by": 0,
            "project_id": 1,
            "valid": True
        },
        {
            "account_name": "Test Account 2",
            "account_type": 2,
            "description": "Test description 2",
            "parent_account": 0,
            "phone": "987-654-3210",
            "website": "www.test2.com",
            "industry": 2,
            "employees": 200,
            "billing_address": "456 Test Ave",
            "billing_street": "Test Ave",
            "billing_city": "Test Town",
            "billing_state": "TT",
            "billing_post_code": "67890",
            "billing_country": 2,
            "shipping_address": "456 Test Ave",
            "shipping_street": "Test Ave",
            "shipping_city": "Test Town",
            "shipping_state": "TT",
            "shipping_post_code": "67890",
            "shipping_country": 2,
            "assign_to": 2,
            "created_by": 1,
            "updated_by": 1,
            "deleted_by": 0,
            "project_id": 1,
            "valid": True
        }
    ]
    
    for account_data in test_accounts:
        create_account(session, **account_data)
    
    print("Test accounts created.")

# Verification function
def verify_crud_operations(session):
    print("\nVerifying CRUD operations:")
    
    # Create
    new_account = create_account(session, 
                                 account_name="Verification Account",
                                 account_type=3,
                                 description="Verification description",
                                 parent_account=0,
                                 phone="555-123-4567",
                                 website="www.verify.com",
                                 industry=3,
                                 employees=50,
                                 billing_address="789 Verify Rd",
                                 billing_street="Verify Rd",
                                 billing_city="Verify City",
                                 billing_state="VC",
                                 billing_post_code="54321",
                                 billing_country=3,
                                 shipping_address="789 Verify Rd",
                                 shipping_street="Verify Rd",
                                 shipping_city="Verify City",
                                 shipping_state="VC",
                                 shipping_post_code="54321",
                                 shipping_country=3,
                                 assign_to=3,
                                 created_by=1,
                                 updated_by=1,
                                 deleted_by=0,
                                 project_id=1,
                                 valid=True)
    print(f"Create - New account ID: {new_account.id}")

    # Read
    retrieved_account = read_account(session, new_account.id)
    print(f"Read - Account name: {retrieved_account.account_name}")

    # Update
    updated_account = update_account(session, new_account.id, account_name="Updated Verification Account")
    print(f"Update - Updated account name: {updated_account.account_name}")

    # Delete
    deleted_account = delete_account(session, new_account.id)
    print(f"Delete - Deleted account ID: {deleted_account.id}")

    # Verify deletion
    verified_deletion = read_account(session, new_account.id)
    print(f"Verify deletion - Account exists: {verified_deletion is not None}")


# Main execution
if __name__ == "__main__":
    session = Session()

    # Create test accounts
    create_test_accounts(session)

    # Verify CRUD operations
    verify_crud_operations(session)

    # Get all accounts
    all_accounts = get_all_accounts(session)
    print(f"\nTotal accounts: {len(all_accounts)}")

    # Get accounts by type
    accounts_by_type = get_accounts_by_type(session, 1)
    print(f"Accounts of type 1: {len(accounts_by_type)}")

    # Get account by name
    account_by_name = get_account_by_name(session, "Test Account 1")
    print(f"Account by name: {account_by_name.account_name if account_by_name else 'Not found'}")

    # Count accounts
    total_accounts = count_accounts(session)
    print(f"Total accounts: {total_accounts}")

    # Get accounts by industry
    accounts_by_industry = get_accounts_by_industry(session, 1)
    print(f"Accounts in industry 1: {len(accounts_by_industry)}")

    # Get accounts by city
    accounts_by_city = get_accounts_by_city(session, "Test City")
    print(f"Accounts in Test City: {len(accounts_by_city)}")

    # Get recent accounts
    recent_accounts = get_recent_accounts(session)
    print(f"Recent accounts: {len(recent_accounts)}")

    # Deactivate an account
    deactivated_account = deactivate_account(session, 1)
    print(f"Deactivated account: {deactivated_account.id if deactivated_account else 'Not found'}")

    # Activate an account
    activated_account = activate_account(session, 1)
    print(f"Activated account: {activated_account.id if activated_account else 'Not found'}")

    # Get inactive accounts
    inactive_accounts = get_inactive_accounts(session)
    print(f"Inactive accounts: {len(inactive_accounts)}")

    session.close()