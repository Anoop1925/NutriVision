from flask import Blueprint, request, jsonify
from services.recommendation import generate_custom_recommendations

custom_bp = Blueprint('custom', __name__)


@custom_bp.route('/recommend', methods=['POST'])
def recommend():
    d = request.get_json(force=True)
    nutrition = d.get('nutrition', [500, 50, 0, 0, 400, 100, 10, 10, 10])
    nb = int(d.get('count', 5))
    ingredients = d.get('ingredients', '')
    recipes = generate_custom_recommendations(nutrition, nb, ingredients)
    return jsonify({'recipes': recipes})
