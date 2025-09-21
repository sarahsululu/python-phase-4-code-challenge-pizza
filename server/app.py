#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        response = [r.to_dict(only=("id", "name", "address")) for r in restaurants]
        return response, 200

class RestaurantById(Resource):
    def get(self, id):
        restaurant = db.session.get(Restaurant, id)

        if not restaurant:
            return {"error": "Restaurant not found"}, 404

        response = {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [
                {
                    "id": rp.id,
                    "pizza_id": rp.pizza_id,
                    "restaurant_id": rp.restaurant_id,
                    "price": rp.price,
                    "pizza": {
                        "id": rp.pizza.id,
                        "name": rp.pizza.name,
                        "ingredients": rp.pizza.ingredients,
                    }
                }
                for rp in restaurant.restaurant_pizzas
            ]
        }

        return response, 200

    def delete(self, id):
        restaurant = db.session.get(Restaurant, id)

        if not restaurant:
            return {"error": "Restaurant not found"}, 404

        RestaurantPizza.query.filter_by(restaurant_id=id).delete()

        db.session.delete(restaurant)
        db.session.commit()

        return "", 204

class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        response = [{"id": p.id, "name": p.name, "ingredients": p.ingredients} for p in pizzas]
        return response, 200

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json() or {}
        price = data.get("price")
        pizza_id = data.get("pizza_id")
        restaurant_id = data.get("restaurant_id")

        errors = []

        if price is None or not isinstance(price, (int, float)) or not (1 <= price <= 30):
            errors.append("validation errors")

        pizza = db.session.get(Pizza, pizza_id)
        if not pizza:
            errors.append("validation errors")

        restaurant = db.session.get(Restaurant, restaurant_id)
        if not restaurant:
            errors.append("validation errors")

        if errors:
            return {"errors": errors}, 400

        new_rp = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_rp)
        db.session.commit()

        response = {
            "id": new_rp.id,
            "pizza_id": new_rp.pizza_id,
            "restaurant_id": new_rp.restaurant_id,
            "price": new_rp.price,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }

        return response, 201

api.add_resource(Restaurants, "/restaurants")
api.add_resource(RestaurantById, "/restaurants/<int:id>")
api.add_resource(Pizzas, "/pizzas")
api.add_resource(RestaurantPizzas, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)
