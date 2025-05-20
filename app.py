from flask import Flask, request, render_template, redirect, session, url_for, jsonify
from werkzeug.utils import secure_filename
from llm_chat import extract_command
from menu_utils import (
    load_menu,
    save_menu_data,
    filter_menu_by_allergy,
    only_menu_with_allergy,
    filter_by_vegan_level
)
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    menu = load_menu()
    user_input = ""
    result = menu

    if request.method == 'POST':
        user_input = request.form.get("message")
        command = extract_command(user_input)

        if command["action"] == "filter":
            if command["target"] == "allergy":
                result = filter_menu_by_allergy(menu, command["value"])
            elif command["target"] == "vegan_level":
                result = filter_by_vegan_level(menu, command["value"])
        elif command["action"] == "only":
            result = only_menu_with_allergy(menu, command["value"])
        elif command["action"] == "reset":
            result = menu

    cart = session.get("cart", {})
    if isinstance(cart, list):
        cart = {}

    cart_items = []
    for item in menu:
        item_id = str(item["id"])
        if item_id in cart:
            item_copy = item.copy()
            item_copy["quantity"] = cart[item_id]
            cart_items.append(item_copy)

    return render_template("index.html", menu=result, user_input=user_input, cart_items=cart_items)

@app.route('/add_to_cart/<int:menu_id>')
def add_to_cart(menu_id):
    cart = session.get("cart", {})
    if isinstance(cart, list):
        cart = {}
    menu_id_str = str(menu_id)
    cart[menu_id_str] = cart.get(menu_id_str, 0) + 1
    session["cart"] = cart
    return redirect(url_for("index"))

@app.route('/clear_cart')
def clear_cart():
    session["cart"] = {}
    return redirect(url_for("index"))

@app.route('/api/increase_quantity', methods=['POST'])
def api_increase_quantity():
    data = request.get_json()
    menu_id = str(data.get("menu_id"))
    cart = session.get("cart", {})
    cart[menu_id] = cart.get(menu_id, 0) + 1
    session["cart"] = cart
    return jsonify({"id": menu_id, "quantity": cart[menu_id]})

@app.route('/api/decrease_quantity', methods=['POST'])
def api_decrease_quantity():
    data = request.get_json()
    menu_id = str(data.get("menu_id"))
    cart = session.get("cart", {})
    if menu_id in cart:
        cart[menu_id] -= 1
        if cart[menu_id] <= 0:
            del cart[menu_id]
    session["cart"] = cart
    return jsonify({"id": menu_id, "quantity": cart.get(menu_id, 0)})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    menu = load_menu()
    if request.method == 'POST':
        if 'delete_id' in request.form:
            delete_id = int(request.form['delete_id'])
            menu = [item for item in menu if item['id'] != delete_id]
            save_menu_data(menu)
            return redirect(url_for('admin'))

        name = request.form.get('name')
        price = int(request.form.get('price'))
        category = request.form.get('category')
        vegan_level = request.form.get('vegan_level')
        allergy = request.form.getlist('allergy')
        image_file = request.files.get('image')

        image_filename = ""
        if image_file and allowed_file(image_file.filename):
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)

        new_id = max([item['id'] for item in menu], default=0) + 1
        new_menu = {
            "id": new_id,
            "name": name,
            "price": price,
            "category": category,
            "image": image_filename,
            "allergy": allergy,
            "vegan_level": vegan_level
        }
        menu.append(new_menu)
        save_menu_data(menu)
        return redirect(url_for('admin'))

    return render_template("admin.html", menu=menu)

if __name__ == '__main__':
    app.run(debug=True)
