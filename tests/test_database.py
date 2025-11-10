import pytest
from sqlalchemy import text
from app.config.database import get_db

@pytest.mark.asyncio
async def test_db_connection():
    """Tests that the database connection is successful."""
    try:
        async for db in get_db():
            result = await db.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Database connection test failed: {e}")
