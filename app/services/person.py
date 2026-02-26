"""
Person model — BMI, BMR, calorie calculations, and diet recommendation generation.
Mirrors the Person class from the original Streamlit app.
"""
from random import uniform as rnd
from GenerateRecommendations import Generator
from ImageFind import get_images_links as find_image


class Person:
    def __init__(self, age, height, weight, gender, food_type, activity, meals_calories_perc, weight_loss):
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender
        self.food_type = food_type
        self.activity = activity
        self.meals_calories_perc = meals_calories_perc
        self.weight_loss = weight_loss

    # ── BMI ──────────────────────────────────────────────
    def calculate_bmi(self):
        return round(self.weight / ((self.height / 100) ** 2), 2)

    def bmi_result(self):
        bmi = self.calculate_bmi()
        if bmi < 18.5:
            category, color = 'Underweight', 'red'
        elif bmi < 25:
            category, color = 'Normal', 'green'
        elif bmi < 30:
            category, color = 'Overweight', 'yellow'
        else:
            category, color = 'Obesity', 'red'
        return {'value': bmi, 'category': category, 'color': color}

    # ── BMR / Calories ───────────────────────────────────
    def calculate_bmr(self):
        if self.gender == 'Male':
            return 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        return 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

    def calories_calculator(self):
        activities = [
            'Little/no exercise', 'Light exercise',
            'Moderate exercise (3-5 days/wk)',
            'Very active (6-7 days/wk)',
            'Extra active (very active & physical job)'
        ]
        weights = [1.2, 1.375, 1.55, 1.725, 1.9]
        w = weights[activities.index(self.activity)]
        return self.calculate_bmr() * w

    def calorie_plans(self):
        maintain = self.calories_calculator()
        plans = [
            {'name': 'Maintain weight', 'calories': round(maintain), 'delta': '-0 kg/week'},
            {'name': 'Mild weight loss', 'calories': round(maintain * 0.9), 'delta': '-0.25 kg/week'},
            {'name': 'Weight loss', 'calories': round(maintain * 0.8), 'delta': '-0.5 kg/week'},
            {'name': 'Extreme weight loss', 'calories': round(maintain * 0.6), 'delta': '-1 kg/week'},
        ]
        return plans

    # ── Recommendation generation ────────────────────────
    def generate_recommendations(self):
        total_calories = self.weight_loss * self.calories_calculator()
        recommendations = []
        for meal, pct in self.meals_calories_perc.items():
            meal_cal = pct * total_calories
            if meal == 'breakfast':
                nv = [meal_cal, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400),
                      rnd(40, 75), rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            elif meal in ('lunch', 'dinner'):
                nv = [meal_cal, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400),
                      rnd(40, 75), rnd(4, 20), rnd(0, 10), rnd(50, 175)]
            else:
                nv = [meal_cal, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400),
                      rnd(40, 75), rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            gen = Generator(nv, food_type=self.food_type)
            recipes = gen.generate()['output']
            recommendations.append({'meal': meal, 'recipes': recipes or []})

        # Attach images
        for group in recommendations:
            for r in group['recipes']:
                r['image_link'] = find_image(r.get('Name', ''))
        return recommendations
