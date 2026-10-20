import os
import sys
import tempfile
import pytest

# Добавляем корень проекта в sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import database

@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path, monkeypatch):
    """
    Каждый тест получает изолированную временную SQLite базу данных.
    Рабочая база litrball.db не затрагивается.
    """
    db_file = tmp_path / "test_litrball.db"
    monkeypatch.setenv("LITRBALL_DB_PATH", str(db_file))
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    
    # Инициализируем схему таблиц
    database.init_db()
    
    yield str(db_file)
