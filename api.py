from flask import Flask, request, jsonify
from flask_cors import CORS
from GenerateRecommendations import Generator
from random import uniform as rnd
from ImageFind import get_images_links as find_image
import fitz
import json
import os
import google.generativeai as genai  # Import the entire module

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow any origin
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

API_KEY = "AIzaSyCgRNgd04AllhAdKTdbDFNlG-ollnwsTTI"

# Configure the API key first
genai.configure(api_key=API_KEY)

# Then initialize the model
model = genai.GenerativeModel("gemini-2.5-flash")  # No need to pass API key here

# Directory containing PDFs
KNOWLEDGE_BASE_PATH = "assets/nutrition_kb"

def load_knowledge_base(disease):
    """Extracts relevant text from PDFs related to the given disease."""
    combined_content = ""

    try:
        files = [f for f in os.listdir(KNOWLEDGE_BASE_PATH) if f.endswith(".pdf")]

        for file in files:
            file_path = os.path.join(KNOWLEDGE_BASE_PATH, file)
            doc = fitz.open(file_path)
            full_text = "\n".join([page.get_text() for page in doc])

            if disease.lower() in full_text.lower():
                relevant_content = extract_relevant_content(full_text, disease)
                combined_content += f"From {file}: {relevant_content}\n\n"

    except Exception as e:
        print("Error loading knowledge base:", e)
        return "Error accessing knowledge base"

    return combined_content or "No relevant information found in knowledge base"

def extract_relevant_content(text, disease):
    """Finds disease-related paragraphs in the text."""
    paragraphs = text.split("\n\n")
    relevant = [p for p in paragraphs if disease.lower() in p.lower()]
    return "\n\n".join(relevant[:3])[:2000] + ("..." if len(relevant) > 3 else "")

class Recommendation:
    def __init__(self,nutrition_input,nb_recommendations,ingredient_txt):
        self.nutrition_input=nutrition_input
        self.nb_recommendations=nb_recommendations
        self.ingredient_txt=ingredient_txt
        pass
    def generate(self,):
        params={'n_neighbors':self.nb_recommendations,'return_distance':False}
        ingredients=self.ingredient_txt.split(';')
        generator=Generator(self.nutrition_input,ingredients,params)
        recommendations=generator.generate()['output']
        # recommendations = recommendations.json()['output']
        if recommendations!=None:              
            for recipe in recommendations:
                recipe['image_link']=find_image(recipe['Name'])
        return recommendations

class Person:

    def __init__(self, age, height, weight, gender, foodType, activity, meals_calories_perc, weight_loss):
        self.age = int(age)
        self.height = float(height)
        self.weight = float(weight)
        self.gender = gender
        self.foodType = foodType
        self.activity = activity
        self.meals_calories_perc = meals_calories_perc
        self.weight_loss = weight_loss

    def print_data(self):
        print(self.age, self.weight, self.meals_calories_perc, self.gender, self.activity)

    def calculate_bmi(self):
        bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        return bmi
    
    def calculate_bmr(self):
        if self.gender == 'Male':
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        return bmr

    def calories_calculator(self):
        activites = ['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)', 'Very active (6-7 days/wk)', 'Extra active (very active & physical job)']
        weights = [1.2, 1.375, 1.55, 1.725, 1.9]
        weight = weights[activites.index(self.activity)]

        maintain_calories = self.calculate_bmr() * weight
        return maintain_calories
    
    def generate_recommendations(self):
        print(self.weight_loss)
        print(self.calories_calculator())
        total_calories = self.weight_loss * self.calories_calculator()
        recommendations = []
        for meal in self.meals_calories_perc:
            meal_calories = self.meals_calories_perc[meal] * total_calories
            if meal == 'breakfast':        
                recommended_nutrition = [meal_calories, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75), rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            elif meal == 'lunch':
                recommended_nutrition = [meal_calories, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75), rnd(4, 20), rnd(0, 10), rnd(50, 175)]
            elif meal == 'dinner':
                recommended_nutrition = [meal_calories, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75), rnd(4, 20), rnd(0, 10), rnd(50, 175)] 
            else:
                recommended_nutrition = [meal_calories, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75), rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            generator = Generator(recommended_nutrition, food_type=self.foodType)
            recommended_recipes = generator.generate()['output']
            for recipe in recommended_recipes:
            # Check for NaN in cookTime and replace with a default value or null
                if 'cookTime' in recipe and (str(recipe['cookTime']).lower() == 'nan' or recipe['cookTime'] is None):
                    recipe['cookTime'] = 0  # or you could use null by setting to None
                
            # Do the same for any other fields that might contain NaN
                for key, value in recipe.items():
                    if str(value).lower() == 'nan':
                        recipe[key] = None
            recommendations.append(recommended_recipes)
        for recommendation in recommendations:
            for recipe in recommendation:
                recipe['image_link'] = find_image(recipe['Name']) 
        return recommendations

@app.route('/recommendations', methods=['POST','OPTIONS'])
def recommend():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.status_code = 200
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')  # Match this with your frontend URL
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    age = data.get('age')
    height = data.get('height')
    weight = data.get('weight')
    gender = data.get('gender')
    foodType = data.get('foodType')
    activity = data.get('activity')
    print(age, height, weight)
    weight_loss = data.get('weight_loss')
    plans=["Maintain weight","Mild weight loss","Weight loss","Extreme weight loss"]
    weights=[1,0.9,0.8,0.6]
    weight_loss = weights[plans.index(weight_loss)]


    number_of_meals = data.get('number_of_meals')

    if not all([age, height, weight, gender, foodType, activity, weight_loss, number_of_meals]):
        return jsonify({"error": "Missing required fields"}), 400

    if number_of_meals == 3:
        meals_calories_perc = {'breakfast': 0.35, 'lunch': 0.40, 'dinner': 0.25}
    elif number_of_meals == 4:
        meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'dinner': 0.25}
    else:
        meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'afternoon snack': 0.05, 'dinner': 0.20}

    person = Person(age, height, weight, gender, foodType, activity, meals_calories_perc, weight_loss)
    person.print_data()
    recommendations = person.generate_recommendations()

    response =  jsonify(recommendations)
   # response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')  # Match this with your frontend URL
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/custom_recommendation', methods=['POST','OPTIONS'])
def custom_recommend():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.status_code = 200
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')  # Allow only your React frontend
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Credentials', 'true')  # If you need cookies
        return response
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    Calories = data.get("Calories")
    FatContent = data.get("FatContent")
    SaturatedFatContent = data.get("SaturatedFatContent")
    CholesterolContent = data.get("CholesterolContent")
    SodiumContent = data.get("SodiumContent")
    CarbohydrateContent = data.get("CarbohydrateContent")
    FiberContent = data.get("FiberContent")
    SugarContent = data.get("SugarContent")
    ProteinContent = data.get("ProteinContent")
    nb_recommendations = data.get("nb_recommendations")
    ingredient_txt= data.get("ingredient_txt")
    nutritions_values_list=[Calories,FatContent,SaturatedFatContent,CholesterolContent,SodiumContent,CarbohydrateContent,FiberContent,SugarContent,ProteinContent]
    recommendation=Recommendation(nutritions_values_list,nb_recommendations,ingredient_txt)
    recommendations=recommendation.generate()

    response =  jsonify(recommendations)
    return response

@app.route("/generate-diet", methods=["POST"])
def generate_diet_plan():
    """Generates a diet plan based on the given disease using Gemini API."""
    data = request.json
    disease = data.get("disease")

    if not disease:
        return jsonify({"error": "Disease is required"}), 400

    knowledge_base = load_knowledge_base(disease)

    prompt = f"""
    Generate a diet plan for {disease} in JSON format.
    Use the following knowledge base information: {knowledge_base}

    Return only a valid JSON object with this structure:
    {{
        "Calories": 1800,
        "FatContent": 55,
        "SaturatedFatContent": 16,
        "CholesterolContent": 200,
        "SodiumContent": 1500,
        "CarbohydrateContent": 200,
        "FiberContent": 35,
        "SugarContent": 25,
        "ProteinContent": 60,
        "description": "This diet is tailored for {disease} by [explanation]"
    }}
    """

    try:
        # Correct way to generate content with Gemini
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        text_response = response.text
        json_match = text_response[text_response.find("{") : text_response.rfind("}") + 1]

        return jsonify(json.loads(json_match))
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Failed to generate diet plan"}), 500


if __name__ == '__main__':
    app.run(debug=True)
