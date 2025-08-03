from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%40JMh05t1@localhost/shopping_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            api_key = request.headers.get('X-API-KEY')
            if not api_key:
                return jsonify({"error": "Missing API key"}), 401
            user = User.query.filter_by(api_key=api_key).first()
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            if user.role not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Define Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('quantity >= 0', name='check_quantity_non_negative'),
    )

# Preload data only once
with app.app_context():
    db.create_all()
    if Product.query.count() == 0:
        products = [
            Product(name="Wireless Mouse", price=799, quantity=20),
            Product(name="Keyboard", price=1299, quantity=15),
            Product(name="Laptop Stand", price=999, quantity=10),
            Product(name="USB-C Hub", price=1499, quantity=12),
            Product(name="Notebook Cooler", price=699, quantity=25),
        ]
        db.session.bulk_save_objects(products)
        db.session.commit()

# Create
@app.route('/products', methods=['POST'])
@require_role('admin')
def add_product():
    data = request.get_json()
    product = Product(name=data['name'], price=data['price'], quantity=data['quantity'])
    db.session.add(product)
    db.session.commit()
    return jsonify({"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity}), 201

# Read All
@app.route('/products', methods=['GET'])
@require_role('admin', 'user')
def get_all_products():
    products = Product.query.all()
    return jsonify([{"id": p.id, "name": p.name, "price": p.price, "quantity": p.quantity} for p in products])

# Read One
@app.route('/products/<int:pid>', methods=['GET'])
@require_role('admin', 'user')
def get_product(pid):
    product = Product.query.get(pid)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity})

# Update
@app.route('/products/<int:pid>', methods=['PUT'])
@require_role('admin')
def update_product(pid):
    product = Product.query.get(pid)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    product.quantity = data.get('quantity', product.quantity)
    db.session.commit()
    return jsonify({"id": product.id, "name": product.name, "price": product.price, "quantity": product.quantity})

# Delete
@app.route('/products/<int:pid>', methods=['DELETE'])
@require_role('admin')
def delete_product(pid):
    product = Product.query.get(pid)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200

# Buy
@app.route('/buy/<int:pid>', methods=['POST'])
@require_role('user')
def buy_product(pid):
    product = Product.query.get(pid)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    data = request.get_json()
    qty = data.get('quantity', 1)
    if product.quantity < qty:
        return jsonify({"error": "Insufficient quantity"}), 400
    product.quantity -= qty
    db.session.commit()
    return jsonify({"message": f"Purchased {qty} item(s)", "product": {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "quantity": product.quantity
    }})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(username=username, api_key=str(uuid.uuid4()), role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered", "api_key": user.api_key}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if user and user.check_password(data.get('password')):
        return jsonify({"message": "Login successful", "api_key": user.api_key, "role": user.role}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
