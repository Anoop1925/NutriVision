import io
from flask import Blueprint, request, jsonify
from PIL import Image
from services.analyzer import analyze_food_image, enrich_analysis

analyzer_bp = Blueprint('analyzer', __name__)


@analyzer_bp.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    image = Image.open(file.stream)
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    raw = buf.getvalue()

    items = analyze_food_image(raw)
    if not items:
        return jsonify({'error': 'Could not analyze image'}), 422

    result = enrich_analysis(items)
    return jsonify(result)
