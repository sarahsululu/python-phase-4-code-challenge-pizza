import pytest
from faker import Faker
from app import app, db
from models import Restaurant, Pizza, RestaurantPizza

@pytest.fixture(scope="module")
def test_app():
    """Set up Flask app context and in-memory SQLite DB for testing."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


class TestRestaurantPizza:
    """Tests for RestaurantPizza model."""

    def test_price_between_1_and_30(self, test_app):
        """Price should accept 1 and 30 without errors."""
        pizza = Pizza(name=Faker().name(), ingredients="Dough, Sauce, Cheese")
        restaurant = Restaurant(name=Faker().name(), address="Main St")
        db.session.add_all([pizza, restaurant])
        db.session.commit()

        rp_low = RestaurantPizza(restaurant_id=restaurant.id, pizza_id=pizza.id, price=1)
        rp_high = RestaurantPizza(restaurant_id=restaurant.id, pizza_id=pizza.id, price=30)
        db.session.add_all([rp_low, rp_high])
        db.session.commit()

        assert rp_low.price == 1
        assert rp_high.price == 30

    def test_price_too_low(self, test_app):
        """Price below 1 should raise ValueError."""
        pizza = Pizza(name=Faker().name(), ingredients="Dough, Sauce, Cheese")
        restaurant = Restaurant(name=Faker().name(), address="Main St")
        db.session.add_all([pizza, restaurant])
        db.session.commit()

        with pytest.raises(ValueError):
            rp = RestaurantPizza(restaurant_id=restaurant.id, pizza_id=pizza.id, price=0)
            db.session.add(rp)
            db.session.commit()

    def test_price_too_high(self, test_app):
        """Price above 30 should raise ValueError."""
        pizza = Pizza(name=Faker().name(), ingredients="Dough, Sauce, Cheese")
        restaurant = Restaurant(name=Faker().name(), address="Main St")
        db.session.add_all([pizza, restaurant])
        db.session.commit()

        with pytest.raises(ValueError):
            rp = RestaurantPizza(restaurant_id=restaurant.id, pizza_id=pizza.id, price=31)
            db.session.add(rp)
            db.session.commit()
