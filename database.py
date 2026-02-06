"""
Database models and configuration for Bank Statement Analyzer.
Uses SQLAlchemy ORM with Supabase PostgreSQL backend.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import streamlit as st
import os

# Database configuration - check st.secrets first, then env vars
DATABASE_URL = st.secrets.get("DATABASE_URL", os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/bank_analyzer"
))

# Create engine
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== DATABASE MODELS ====================

class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # UUID from Supabase Auth
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    statements = relationship("BankStatement", back_populates="user", cascade="all, delete-orphan")
    learned_patterns = relationship("LearnedPattern", back_populates="user", cascade="all, delete-orphan")


class BankStatement(Base):
    """Individual bank statement upload"""
    __tablename__ = "bank_statements"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Statement metadata
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    statement_period = Column(String)

    # Summary data
    total_income = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    net_cash_flow = Column(Float, default=0.0)
    health_score = Column(Float, default=0.0)

    # Raw transaction data (JSON)
    raw_data = Column(JSON, default=list)

    # Relationships
    user = relationship("User", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BankStatement {self.filename} - {self.upload_date}>"


class Transaction(Base):
    """Individual transaction from a statement"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey("bank_statements.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Transaction details
    date = Column(String, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String)  # "credit" or "debit"

    # Categorization
    category = Column(String, nullable=False)  # Primary category
    category_confidence = Column(Float, default=1.0)  # 0-1 confidence score
    user_corrected = Column(Boolean, default=False)  # True if user manually corrected

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    statement = relationship("BankStatement", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.date} - {self.description[:30]} - ${self.amount}>"


class LearnedPattern(Base):
    """User-trained categorization patterns"""
    __tablename__ = "learned_patterns"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Pattern details
    pattern = Column(String, nullable=False)  # Text to match
    category = Column(String, nullable=False)  # Target category
    match_type = Column(String, default="contains")  # "contains", "exact", "startswith"

    # Usage tracking
    times_used = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="learned_patterns")

    def __repr__(self):
        return f"<LearnedPattern '{self.pattern}' -> {self.category}>"


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Create all tables if they don't exist"""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False


# ==================== USER FUNCTIONS ====================

def user_exists(db, user_id: str) -> bool:
    """Check if user exists in database"""
    return db.query(User).filter(User.id == user_id).first() is not None


def create_user(db, user_id: str, email: str):
    """Create a new user record"""
    user = User(id=user_id, email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db, user_id: str):
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


# ==================== STATEMENT FUNCTIONS ====================

def save_statement(db, user_id: str, statement_data: dict):
    """Save a bank statement and return it"""
    statement = BankStatement(
        user_id=user_id,
        filename=statement_data.get("filename", "unknown"),
        statement_period=statement_data.get("statement_period", ""),
        total_income=statement_data.get("total_income", 0.0),
        total_expenses=statement_data.get("total_expenses", 0.0),
        net_cash_flow=statement_data.get("net_cash_flow", 0.0),
        health_score=statement_data.get("health_score", 0.0),
        raw_data=statement_data.get("raw_data", [])
    )
    db.add(statement)
    db.commit()
    db.refresh(statement)
    return statement


def get_user_statements(db, user_id: str):
    """Get all statements for a user, ordered by upload date (newest first)"""
    return db.query(BankStatement).filter(
        BankStatement.user_id == user_id
    ).order_by(BankStatement.upload_date.desc()).all()


def get_statement(db, statement_id: int):
    """Get statement by ID"""
    return db.query(BankStatement).filter(BankStatement.id == statement_id).first()


def delete_statement(db, statement_id: int):
    """Delete statement and all related transactions"""
    statement = get_statement(db, statement_id)
    if statement:
        db.delete(statement)
        db.commit()
        return True
    return False


# ==================== TRANSACTION FUNCTIONS ====================

def save_transactions(db, statement_id: int, user_id: str, transactions: list):
    """Save transactions for a statement"""
    saved = []
    for txn in transactions:
        transaction = Transaction(
            statement_id=statement_id,
            user_id=user_id,
            date=txn.get("date", ""),
            description=txn.get("description", ""),
            amount=txn.get("amount", 0.0),
            transaction_type=txn.get("type", "debit"),
            category=txn.get("category", "Other"),
            category_confidence=txn.get("confidence", 1.0)
        )
        db.add(transaction)
        saved.append(transaction)
    db.commit()
    return saved


def get_statement_transactions(db, statement_id: int):
    """Get all transactions for a statement"""
    return db.query(Transaction).filter(
        Transaction.statement_id == statement_id
    ).order_by(Transaction.date).all()


def update_transaction_category(db, transaction_id: int, new_category: str):
    """Update a transaction's category (user correction)"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if transaction:
        transaction.category = new_category
        transaction.user_corrected = True
        transaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(transaction)
    return transaction


# ==================== LEARNED PATTERN FUNCTIONS ====================

def save_learned_pattern(db, user_id: str, pattern: str, category: str):
    """Save or update a learned pattern"""
    existing = db.query(LearnedPattern).filter(
        LearnedPattern.user_id == user_id,
        LearnedPattern.pattern == pattern
    ).first()

    if existing:
        existing.times_used += 1
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_pattern = LearnedPattern(
            user_id=user_id,
            pattern=pattern,
            category=category
        )
        db.add(new_pattern)
        db.commit()
        db.refresh(new_pattern)
        return new_pattern


def get_user_patterns(db, user_id: str):
    """Get all learned patterns for a user"""
    return db.query(LearnedPattern).filter(
        LearnedPattern.user_id == user_id
    ).order_by(LearnedPattern.times_used.desc()).all()


def apply_learned_patterns(db, user_id: str, description: str):
    """Apply learned patterns to categorize a transaction"""
    patterns = get_user_patterns(db, user_id)
    for p in patterns:
        if p.match_type == "exact" and description.lower() == p.pattern.lower():
            return p.category
        elif p.match_type == "startswith" and description.lower().startswith(p.pattern.lower()):
            return p.category
        elif p.match_type == "contains" and p.pattern.lower() in description.lower():
            return p.category
    return None


def delete_learned_pattern(db, pattern_id: int):
    """Delete a learned pattern"""
    pattern = db.query(LearnedPattern).filter(LearnedPattern.id == pattern_id).first()
    if pattern:
        db.delete(pattern)
        db.commit()
        return True
    return False
