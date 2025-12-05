"""
User model for authentication and user management.

This module defines the User SQLAlchemy model representing users in the database.
Each user has a unique email and user_id, but display names can be duplicated
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.db.base import Base

class User(Base):
    """
    User model for authentication and profile management
    
    Attributes:
        id: Unique user identifier (primary key)
        email: Unique email address for authentication
        password_hash: Bcrypt hashed password
        display_name: User's display name (for UI display)
        is_active: Account status flag (for soft deletion/suspension)
        created_at: Account creation timestamp
        last_login: Most recent successful login timestamp
    """
    __tablename__ = "users"

    # Primary key - unique identifier for each user
    id = Column(Integer, primary_key=True, index=True)

    # Authentication fields
    email = Column(
        String(255),
        unique=True, # Enforce email uniqueness at database level
        nullable=False,
        index=True # Index for fast lookups during login
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    # Profile fields
    display_name = Column(
        String(100),
        nullable=False
    )

    # Status fields
    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    # Timestamps for auditing and analytics
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    last_login = Column(
        DateTime,
        nullable=True
    )

    # TODO: Relationships
    # Commented out until related models are created
    # group_membershuips = relationship("GroupMember", back_populates="user")
    # piglists = relationship("Piglist", back_populates="user")
    # purchased_gifts = relationship("Gift", foreign_keys="Gift.purchased_by")

    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"<User(id={self.id}, "
            f"email='{self.email}', "
            f"display_name='{self.display_name}')>"
        )
    
    