from database.models import SessionLocal, Opportunity

db = SessionLocal()

# Delete all rows from opportunities table
db.query(Opportunity).delete()
db.commit()
db.close()

print("✅ Cleared all records from opportunities table")
