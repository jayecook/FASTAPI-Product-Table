from database import Base, engine, SessionLocal
from models import User, Product
from auth import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

admin_username = "admin"
admin_password = "admin123"

existing_admin = db.query(User).filter(User.username == admin_username).first()
if not existing_admin:
    admin_user = User(
        username=admin_username,
        password_hash=hash_password(admin_password),
        role="admin"
    )
    db.add(admin_user)
    print("Admin user created.")
else:
    print("Admin user already exists.")

# Delete existing products first
db.query(Product).delete()

# Always re-add products
starter_products = [
    Product(name="Standard Steel Hammer", stock=25, amount=50),
    Product(name="Nails", stock=16, amount=100),
    Product(name="Screw Drivers", stock=55, amount=150),
    Product(name="Screws", stock=87, amount=200),
    Product(name="Weighted Handle Hammer", stock=22, amount=150),
    Product(name="Hammer", stock=25, amount=50),
    Product(name="Skinny Nails", stock=25, amount=50),
    Product(name="Hammer", stock=25, amount=50),
    Product(name="Hammer", stock=25, amount=50),
    Product(name="Hammer", stock=25, amount=50),
    Product(name="Hammer", stock=25, amount=50),
]

db.add_all(starter_products)
print("Products refreshed.")

db.commit()
db.close()

print("Database setup complete.")