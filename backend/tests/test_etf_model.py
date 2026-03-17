"""Tests for EtfCustomSymbol model."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.etf_custom_symbol import EtfCustomSymbol  # register with Base.metadata


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_and_retrieve_custom_symbol(db):
    from app.models.etf_custom_symbol import EtfCustomSymbol
    sym = EtfCustomSymbol(symbol="TQQQ")
    db.add(sym)
    db.commit()

    result = db.query(EtfCustomSymbol).filter_by(symbol="TQQQ").first()
    assert result is not None
    assert result.symbol == "TQQQ"
    assert result.added_at is not None


def test_symbol_is_primary_key(db):
    from app.models.etf_custom_symbol import EtfCustomSymbol
    from sqlalchemy.exc import IntegrityError
    db.add(EtfCustomSymbol(symbol="TQQQ"))
    db.commit()
    db.add(EtfCustomSymbol(symbol="TQQQ"))
    with pytest.raises(IntegrityError):
        db.commit()
