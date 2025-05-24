# app/db/init_db.py

from app.db.session import SessionLocal

def test_connection():
    try:
        db = SessionLocal()
        print("✅ Database connection successful!")
    except Exception as e:
        print("❌ Database connection failed:", str(e))
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
