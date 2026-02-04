"""Tests for SQLAlchemy declarative base and mixins."""

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase

from src.db.base import Base, TimestampMixin


class TestBase:
    """Tests for the Base declarative class."""

    def test_base_is_declarative_base(self) -> None:
        """Test that Base inherits from DeclarativeBase."""
        assert issubclass(Base, DeclarativeBase)

    def test_base_can_be_subclassed(self) -> None:
        """Test that Base can be used as a base for models."""
        # The fact that User and other models exist proves this,
        # but verify explicitly that subclassing works.
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


class TestTimestampMixin:
    """Tests for the TimestampMixin class."""

    def test_created_at_column_exists(self) -> None:
        """Test that TimestampMixin has a created_at mapped column."""
        col = TimestampMixin.__dict__["created_at"]
        assert col is not None

    def test_updated_at_column_exists(self) -> None:
        """Test that TimestampMixin has an updated_at mapped column."""
        col = TimestampMixin.__dict__["updated_at"]
        assert col is not None

    def test_created_at_column_type_is_datetime_with_timezone(self) -> None:
        """Test that created_at uses DateTime(timezone=True)."""
        col = TimestampMixin.__dict__["created_at"]
        # Access the underlying column descriptor
        column = col.column
        assert isinstance(column.type, DateTime)
        assert column.type.timezone is True

    def test_updated_at_column_type_is_datetime_with_timezone(self) -> None:
        """Test that updated_at uses DateTime(timezone=True)."""
        col = TimestampMixin.__dict__["updated_at"]
        column = col.column
        assert isinstance(column.type, DateTime)
        assert column.type.timezone is True

    def test_created_at_is_not_nullable(self) -> None:
        """Test that created_at column is not nullable."""
        col = TimestampMixin.__dict__["created_at"]
        column = col.column
        assert column.nullable is False

    def test_updated_at_is_not_nullable(self) -> None:
        """Test that updated_at column is not nullable."""
        col = TimestampMixin.__dict__["updated_at"]
        column = col.column
        assert column.nullable is False

    def test_updated_at_has_onupdate(self) -> None:
        """Test that updated_at column has an onupdate trigger."""
        col = TimestampMixin.__dict__["updated_at"]
        column = col.column
        assert column.onupdate is not None

    def test_created_at_has_server_default(self) -> None:
        """Test that created_at column has a server_default."""
        col = TimestampMixin.__dict__["created_at"]
        column = col.column
        assert column.server_default is not None
