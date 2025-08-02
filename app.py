from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory DB
products = {
    1: {"id": 1, "name": "Wireless Mouse", "price": 799, "quantity": 20},
    2: {"id": 2, "name": "Keyboard", "price": 1299, "quantity": 15},
    3: {"id": 3, "name": "Laptop Stand", "price": 999, "quantity": 10},
    4: {"id": 4, "name": "USB-C Hub", "price": 1499, "quantity": 12},
    5: {"id": 5, "name": "Notebook Cooler", "price": 699, "quantity": 25},
}
product_id_counter = 6

@app.route('/products', methods=['POST'])
def add_product():
    global product_id_counter
    data = request.get_json()
    product = {
        "id": product_id_counter,
        "name": data['name'],
        "price": data['price'],
        "quantity": data['quantity']
    }
    products[product_id_counter] = product
    product_id_counter += 1
    return jsonify(product), 201

@app.route('/products', methods=['GET'])
def get_all_products():
    return jsonify(list(products.values()))

@app.route('/products/<int:pid>', methods=['GET'])
def get_product(pid):
    product = products.get(pid)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)

@app.route('/products/<int:pid>', methods=['PUT'])
def update_product(pid):
    if pid not in products:
        return jsonify({"error": "Product not found"}), 404
    data = request.get_json()
    products[pid].update(data)
    return jsonify(products[pid])

@app.route('/products/<int:pid>', methods=['DELETE'])
def delete_product(pid):
    if pid not in products:
        return jsonify({"error": "Product not found"}), 404
    del products[pid]
    return jsonify({"message": "Deleted"}), 200

@app.route('/buy/<int:pid>', methods=['POST'])
def buy_product(pid):
    data = request.get_json()
    qty = data.get('quantity', 1)
    if pid not in products:
        return jsonify({"error": "Product not found"}), 404
    if products[pid]['quantity'] < qty:
        return jsonify({"error": "Insufficient quantity"}), 400
    products[pid]['quantity'] -= qty
    return jsonify({"message": f"Purchased {qty} item(s)", "product": products[pid]}), 200

if __name__ == '__main__':
    app.run(debug=True)
