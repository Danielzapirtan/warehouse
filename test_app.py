import pytest, gradio
from app import db, display_db_state, create_product

def test_empty_database():
    assert display_db_state() == "Database is empty."

def test_create_product():
    result = create_product("Test", "units")
    assert "Test (units)" in result
    assert len(db.products) == 1
