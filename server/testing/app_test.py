from server.models import Restaurant, RestaurantPizza, Pizza
from server.app import app, db
from faker import Faker
import pytest


class TestApp:
    """Tests for the Flask app in app.py"""

    @pytest.fixture(autouse=True, scope="class")
    def setup_teardown(self):
        """Setup a clean in-memory database for each test class"""
        # Ensure isolated in-memory DB
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['TESTING'] = True

        with app.app_context():
            db.create_all()
            yield
            db.session.remove()
            db.drop_all()

    def test_restaurants(self):
        """Retrieves all restaurants via GET /restaurants"""
        fake = Faker()
        restaurant1 = Restaurant(name=fake.name(), address=fake.address())
        restaurant2 = Restaurant(name=fake.name(), address=fake.address())
        db.session.add_all([restaurant1, restaurant2])
        db.session.commit()

        response = app.test_client().get('/restaurants')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        response_json = response.json

        assert [r['id'] for r in response_json] == [restaurant1.id, restaurant2.id]
        assert [r['name'] for r in response_json] == [restaurant1.name, restaurant2.name]
        assert [r['address'] for r in response_json] == [restaurant1.address, restaurant2.address]

        for r in response_json:
            assert 'restaurant_pizzas' not in r

    def test_restaurants_id(self):
        """Retrieves a single restaurant via GET /restaurants/<id>"""
        fake = Faker()
        restaurant = Restaurant(name=fake.name(), address=fake.address())
        db.session.add(restaurant)
        db.session.commit()

        response = app.test_client().get(f'/restaurants/{restaurant.id}')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        response_json = response.json

        assert response_json['id'] == restaurant.id
        assert response_json['name'] == restaurant.name
        assert response_json['address'] == restaurant.address
        assert 'restaurant_pizzas' in response_json

    def test_returns_404_if_no_restaurant_to_get(self):
        """Returns 404 if GET /restaurants/<id> with non-existent id"""
        response = app.test_client().get('/restaurants/0')
        assert response.status_code == 404
        assert response.content_type == 'application/json'
        assert 'error' in response.json

    def test_deletes_restaurant_by_id(self):
        """Deletes a restaurant via DELETE /restaurants/<id>"""
        fake = Faker()
        restaurant = Restaurant(name=fake.name(), address=fake.address())
        db.session.add(restaurant)
        db.session.commit()

        response = app.test_client().delete(f'/restaurants/{restaurant.id}')
        assert response.status_code == 204

        result = db.session.get(Restaurant, restaurant.id)
        assert result is None

    def test_returns_404_if_no_restaurant_to_delete(self):
        """Returns 404 if DELETE /restaurants/<id> with non-existent id"""
        response = app.test_client().delete('/restaurants/0')
        assert response.status_code == 404
        assert response.json.get('error') == "Restaurant not found"

    def test_pizzas(self):
        """Retrieves all pizzas via GET /pizzas"""
        fake = Faker()
        pizza1 = Pizza(name=fake.name(), ingredients=fake.sentence())
        pizza2 = Pizza(name=fake.name(), ingredients=fake.sentence())
        db.session.add_all([pizza1, pizza2])
        db.session.commit()

        response = app.test_client().get('/pizzas')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        response_json = response.json

        assert [p['id'] for p in response_json] == [pizza1.id, pizza2.id]
        assert [p['name'] for p in response_json] == [pizza1.name, pizza2.name]
        assert [p['ingredients'] for p in response_json] == [pizza1.ingredients, pizza2.ingredients]

        for p in response_json:
            assert 'restaurant_pizzas' not in p

    def test_creates_restaurant_pizzas(self):
        """Creates a RestaurantPizza via POST /restaurant_pizzas"""
        fake = Faker()
        pizza = Pizza(name=fake.name(), ingredients=fake.sentence())
        restaurant = Restaurant(name=fake.name(), address=fake.address())
        db.session.add_all([pizza, restaurant])
        db.session.commit()

        restaurant_pizza = RestaurantPizza.query.filter_by(
            pizza_id=pizza.id, restaurant_id=restaurant.id
        ).one_or_none()
        if restaurant_pizza:
            db.session.delete(restaurant_pizza)
            db.session.commit()

        response = app.test_client().post(
            '/restaurant_pizzas',
            json={
                "price": 3,
                "pizza_id": pizza.id,
                "restaurant_id": restaurant.id
            }
        )

        assert response.status_code == 201
        assert response.content_type == 'application/json'

        response_json = response.json
        assert response_json['price'] == 3
        assert response_json['pizza']['id'] == pizza.id
        assert response_json['restaurant']['id'] == restaurant.id
        assert response_json.get('id') is not None
        assert response_json.get('pizza') is not None
        assert response_json.get('restaurant') is not None

        query_result = RestaurantPizza.query.filter_by(
            pizza_id=pizza.id, restaurant_id=restaurant.id
        ).first()
        assert query_result.price == 3

    def test_400_for_validation_error(self):
        """Returns 400 if POST /restaurant_pizzas fails validation"""
        fake = Faker()
        pizza = Pizza(name=fake.name(), ingredients=fake.sentence())
        restaurant = Restaurant(name=fake.name(), address=fake.address())
        db.session.add_all([pizza, restaurant])
        db.session.commit()

        # Price too low
        response = app.test_client().post(
            '/restaurant_pizzas',
            json={"price": 0, "pizza_id": pizza.id, "restaurant_id": restaurant.id}
        )
        assert response.status_code == 400
        assert response.json['errors'] == ["validation errors"]

        # Price too high
        response = app.test_client().post(
            '/restaurant_pizzas',
            json={"price": 31, "pizza_id": pizza.id, "restaurant_id": restaurant.id}
        )
        assert response.status_code == 400
        assert response.json['errors'] == ["validation errors"]
