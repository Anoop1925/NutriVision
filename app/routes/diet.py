from flask import Blueprint, request, jsonify
from services.person import Person

diet_bp = Blueprint('diet', __name__)

PLANS = {
    'Maintain weight':      {'weight': 1.0, 'delta': '-0 kg/week'},
    'Mild weight loss':     {'weight': 0.9, 'delta': '-0.25 kg/week'},
    'Weight loss':          {'weight': 0.8, 'delta': '-0.5 kg/week'},
    'Extreme weight loss':  {'weight': 0.6, 'delta': '-1 kg/week'},
}


@diet_bp.route('/calculate', methods=['POST'])
def calculate():
    """Return BMI, BMR, calorie plans — fast, no ML."""
    d = request.get_json(force=True)
    person = _build_person(d)
    bmi = person.bmi_result()
    plans = person.calorie_plans()
    return jsonify({'bmi': bmi, 'plans': plans})


@diet_bp.route('/recommend', methods=['POST'])
def recommend():
    """Generate full diet recommendations (slow — ML + image fetch)."""
    d = request.get_json(force=True)
    person = _build_person(d)
    recommendations = person.generate_recommendations()
    return jsonify({'recommendations': recommendations})


def _build_person(d):
    plan_name = d.get('plan', 'Maintain weight')
    weight_loss = PLANS.get(plan_name, PLANS['Maintain weight'])['weight']

    n_meals = int(d.get('meals', 3))
    if n_meals == 3:
        perc = {'breakfast': 0.35, 'lunch': 0.40, 'dinner': 0.25}
    elif n_meals == 4:
        perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'dinner': 0.25}
    else:
        perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'afternoon snack': 0.05, 'dinner': 0.20}

    return Person(
        age=int(d.get('age', 25)),
        height=int(d.get('height', 170)),
        weight=int(d.get('weight', 70)),
        gender=d.get('gender', 'Male'),
        food_type=d.get('foodType', 'Veg'),
        activity=d.get('activity', 'Little/no exercise'),
        meals_calories_perc=perc,
        weight_loss=weight_loss,
    )
