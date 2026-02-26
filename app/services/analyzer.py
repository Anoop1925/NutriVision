"""
Food image analysis service — uses Gemini to detect food items and nutrition.
"""
import io
import json
from PIL import Image
import google.generativeai as genai

API_KEY = "AIzaSyCgRNgd04AllhAdKTdbDFNlG-ollnwsTTI"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

NUTRITION_KEYS = [
    'Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent',
    'SodiumContent', 'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent'
]

PROMPT = """
Analyze the food in this image. For each food item:
1. Identify the item and its quantity (e.g., 5 bananas, 1 plate of momos with chutney).
2. For composite dishes (e.g., momos with chutney and salad), break down components.
3. Provide nutritional information per unit including:
   - Calories (kcal), FatContent (g), SaturatedFatContent (g), CholesterolContent (mg),
     SodiumContent (mg), CarbohydrateContent (g), FiberContent (g), SugarContent (g), ProteinContent (g)
4. Specify serving size per unit.
Return the response in JSON format with fields: item_name, quantity, serving_size, nutrition_per_unit.
Example:
```json
[
    {
        "item_name": "Banana",
        "quantity": 5,
        "serving_size": "1 medium banana (120g)",
        "nutrition_per_unit": {
            "Calories": 90, "FatContent": 0.3, "SaturatedFatContent": 0.1,
            "CholesterolContent": 0, "SodiumContent": 1, "CarbohydrateContent": 23,
            "FiberContent": 2.6, "SugarContent": 12, "ProteinContent": 1.1
        }
    }
]
```
"""


def analyze_food_image(image_bytes: bytes):
    """Analyse raw image bytes and return a list of detected food items."""
    try:
        response = model.generate_content([
            PROMPT,
            {"inline_data": {"data": image_bytes, "mime_type": "image/png"}}
        ])
        text = response.text.strip('```json\n').strip('```')
        return json.loads(text)
    except (json.JSONDecodeError, Exception):
        return []


def health_status(nutrition: dict, quantity: int):
    """Return health status and weight impact for a food item."""
    scaled = {k: nutrition.get(k, 0) * quantity for k in NUTRITION_KEYS}
    cal, sugar, fat, fiber = scaled['Calories'], scaled['SugarContent'], scaled['FatContent'], scaled['FiberContent']

    if sugar < 25 and fat < 20 and cal < 500:
        status, color = 'Healthy', 'green'
    elif sugar < 50 and fat < 40 and cal < 1000:
        status, color = 'Moderate', 'yellow'
    else:
        status, color = 'Unhealthy', 'red'

    if cal < 300 and fiber > 5:
        impact = 'Supports Weight Loss'
    elif cal > 600:
        impact = 'Supports Weight Gain'
    else:
        impact = 'Supports Weight Maintenance'

    return status, color, impact


def enrich_analysis(items):
    """Add per-item totals, health status, and grand totals."""
    enriched = []
    grand_total = {k: 0 for k in NUTRITION_KEYS}

    for item in items:
        qty = item.get('quantity', 1)
        npu = item.get('nutrition_per_unit', {})
        total = {k: round(npu.get(k, 0) * qty, 1) for k in NUTRITION_KEYS}
        status, color, impact = health_status(npu, qty)

        for k in NUTRITION_KEYS:
            grand_total[k] += total[k]

        enriched.append({
            'item_name': item.get('item_name', 'Unknown'),
            'quantity': qty,
            'serving_size': item.get('serving_size', 'N/A'),
            'nutrition_per_unit': {k: round(npu.get(k, 0), 1) for k in NUTRITION_KEYS},
            'total_nutrition': total,
            'health_status': status,
            'health_color': color,
            'weight_impact': impact,
        })

    grand_total = {k: round(v, 1) for k, v in grand_total.items()}
    g_status, g_color, g_impact = health_status(grand_total, 1)

    return {
        'items': enriched,
        'grand_total': grand_total,
        'overall_status': g_status,
        'overall_color': g_color,
        'overall_impact': g_impact,
    }
