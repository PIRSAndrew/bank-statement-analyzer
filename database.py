"""
Database models and configuration for Bank Statement Analyzer.
Uses SQLAlchemy ORM with Supabase PostgreSQL backend.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Database configuration
DATABASE_URL = os.getenv(
      "DATABASE_URL",
      "postgresql://user:password@localhost/bank_analyzer"
)

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
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    statement_month = Column(String)  # e.g., "2026-02"

    # Metadata
    total_transactions = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    net_cash_flow = Column(Float, default=0.0)
    health_score = Column(Float, default=0.0)

    # Raw data storage (for re-processing if needed)
    raw_data = Column(JSON)  # Stores original extracted transactions

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan")

    def __repr__(self):
              return f"<BankStatement {self.filename} - {self.upload_date.date()}>"


class Transaction(Base):
      """Individual transaction within a statement"""
      __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey("bank_statements.id"), nullable=False)

    # Transaction details
    date = Column(String, nullable=False)  # "MM/DD" or "YYYY-MM-DD"
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

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

    # Metadata
    times_used = Column(Integer, default=1)  # How many times this pattern was applied
    confidence = Column(Float, default=1.0)  # 0-1 confidence in this pattern
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="learned_patterns")

    def __repr__(self):
              return f"<LearnedPattern '{self.pattern}' -> {self.category}>"


# ==================== DATABASE FUNCTIONS ====================

def get_db():
      """Get database session"""
      db = SessionLocal()
      try:
                yield db
finally:
        db.close()


def init_db():
      """Initialize database tables"""
      Base.metadata.create_all(bind=engine)
      print("✅ Database tables created successfully")


# ==================== USER FUNCTIONS ====================

def create_user(db, user_id: str, email: str):
      """Create new user"""
      db_user = User(id=user_id, email=email)
      db.add(db_user)
      db.commit()
      db.refresh(db_user)
      return db_user


def get_user(db, user_id: str):
      """Get user by ID"""
      return db.query(User).filter(User.id == user_id).first()


def user_exists(db, user_id: str):
      """Check if user exists"""
      return db.query(User).filter(User.id == user_id).first() is not None


# ==================== STATEMENT FUNCTIONS ====================

def create_statement(db, user_id: str, filename: str, statement_data: dict):
      """Create new bank statement record"""
      statement = BankStatement(
          user_id=user_id,
          filename=filename,
          statement_month=statement_data.get("statement_month"),
          total_transactions=statement_data.get("total_transactions", 0),
          total_revenue=statement_data.get("total_revenue", 0.0),
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

def add_transaction(db, statement_id: int, transaction_data: dict):
      """Add transaction to statement"""
    transaction = Transaction(
              statement_id=statement_id,
              date=transaction_data["date"],
              description=transaction_data["description"],
              amount=transaction_data["amount"],
              category=transaction_data.get("category", "OTHER_EXPENSE"),
              category_confidence=transaction_data.get("category_confidence", 1.0),
              user_corrected=transaction_data.get("user_corrected", False)
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def add_transactions_bulk(db, statement_id: int, transactions: list):
      """Add multiple transactions at once"""
    transaction_objs = [
              Transaction(
                            statement_id=statement_id,
                            date=t["date"],
                            description=t["description"],
                            amount=t["amount"],
                            category=t.get("category", "OTHER_EXPENSE"),
                            category_confidence=t.get("category_confidence", 1.0),
                            user_corrected=t.get("user_corrected", False)
              )
              for t in transactions
    ]
    db.add_all(transaction_objs)
    db.commit()
    return transaction_objs


def get_statement_transactions(db, statement_id: int):
      """Get all transactions for a statement"""
    return db.query(Transaction).filter(
              Transaction.statement_id == statement_id
    ).order_by(Transaction.date).all()


def update_transaction_category(db, transaction_id: int, category: str):
      """Update transaction category (user correction)"""
      transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
      if transaction:
                transaction.category = category
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
    ).order_by(LearnedPattern.updated_at.desc()).all()


def delete_pattern(db, pattern_id: int):
      """Delete a learned pattern"""
    pattern = db.query(LearnedPattern).filter(LearnedPattern.id == pattern_id).first()
    if pattern:
              db.delete(pattern)
              db.commit()
              return True
          return False
