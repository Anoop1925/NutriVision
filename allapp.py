# deactivate
# rm -rf venv
# python -m venv venv
# .\venv\Scripts\activate
# pip install streamlit==1.49.1 google-generativeai==0.8.3 pandas==2.3.2 pillow==11.0.0 streamlit-echarts==0.4.0



import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io
from GenerateRecommendations import Generator
from random import uniform as rnd
from ImageFind import get_images_links as find_image
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Diet & Food Recommendation", page_icon="🍽️", layout="wide")

# Configure Gemini API
API_KEY = "AIzaSyCgRNgd04AllhAdKTdbDFNlG-ollnwsTTI"
genai.configure(api_key=API_KEY)
# Note: Using gemini-1.5-flash as it's the latest vision model (Sep 2025). Change to gemini-2.5-flash if you have specific access.
model = genai.GenerativeModel('gemini-2.5-flash')

# Nutrition values
nutrition_values = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent', 'SodiumContent', 
                    'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']

# Initialize session state
if 'diet_generated' not in st.session_state:
    st.session_state.diet_generated = False
    st.session_state.diet_recommendations = None
    st.session_state.person = None
    st.session_state.weight_loss_option = None
if 'custom_generated' not in st.session_state:
    st.session_state.custom_generated = False
    st.session_state.custom_recommendations = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
    st.session_state.uploaded_image = None

class Person:
    def __init__(self, age, height, weight, gender, foodType, activity, meals_calories_perc, weight_loss):
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender
        self.foodType = foodType
        self.activity = activity
        self.meals_calories_perc = meals_calories_perc
        self.weight_loss = weight_loss

    def calculate_bmi(self):
        bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        return bmi

    def display_result(self):
        bmi = self.calculate_bmi()
        bmi_string = f'{bmi} kg/m²'
        if bmi < 18.5:
            category = 'Underweight'
            color = 'Red'
        elif 18.5 <= bmi < 25:
            category = 'Normal'
            color = 'Green'
        elif 25 <= bmi < 30:
            category = 'Overweight'
            color = 'Yellow'
        else:
            category = 'Obesity'
            color = 'Red'
        return bmi_string, category, color

    def calculate_bmr(self):
        if self.gender == 'Male':
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        return bmr

    def calories_calculator(self):
        activities = ['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)', 
                      'Very active (6-7 days/wk)', 'Extra active (very active & physical job)']
        weights = [1.2, 1.375, 1.55, 1.725, 1.9]
        weight = weights[activities.index(self.activity)]
        maintain_calories = self.calculate_bmr() * weight
        return maintain_calories

    def generate_recommendations(self):
        total_calories = self.weight_loss * self.calories_calculator()
        recommendations = []
        for meal in self.meals_calories_perc:
            meal_calories = self.meals_calories_perc[meal] * total_calories
            if meal == 'breakfast':
                recommended_nutrition = [meal_calories, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400), 
                                        rnd(40, 75), rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            elif meal == 'lunch':
                recommended_nutrition = [meal_calories, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400), 
                                        rnd(40, 75), rnd(4, 20), rnd(0, 10), rnd(50, 175)]
            elif meal == 'dinner':
                recommended_nutrition = [meal_calories, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400), 
                                        rnd(40, 75), rnd(4, 20), rnd(0, 10), rnd(50, 175)]
            else:
                recommended_nutrition = [meal_calories, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400), 
                                        rnd(40, 75), rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            generator = Generator(recommended_nutrition, food_type=self.foodType)
            recommended_recipes = generator.generate()['output']
            recommendations.append(recommended_recipes)
        for recommendation in recommendations:
            for recipe in recommendation:
                recipe['image_link'] = find_image(recipe.get('Name', ''))
        return recommendations

class Recommendation:
    def __init__(self, nutrition_input, nb_recommendations, ingredient_txt):
        self.nutrition_input = nutrition_input
        self.nb_recommendations = nb_recommendations
        self.ingredient_txt = ingredient_txt

    def generate(self):
        params = {'n_neighbors': self.nb_recommendations, 'return_distance': False}
        ingredients = self.ingredient_txt.split(';') if self.ingredient_txt else []
        generator = Generator(self.nutrition_input, ingredients, params)
        recommendations = generator.generate()['output']
        if recommendations:
            for recipe in recommendations:
                recipe['image_link'] = find_image(recipe.get('Name', ''))
        return recommendations

def analyze_food_image(image):
    """Analyze the uploaded image using Gemini to detect food items and quantities."""
    try:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        prompt = """
        Analyze the food in this image. For each food item:
        1. Identify the item and its quantity (e.g., 5 bananas, 1 plate of momos with chutney).
        2. For composite dishes (e.g., momos with chutney and salad), break down components.
        3. Provide nutritional information per unit (e.g., 1 banana, 1 momo) including:
           - Calories (kcal)
           - FatContent (g)
           - SaturatedFatContent (g)
           - CholesterolContent (mg)
           - SodiumContent (mg)
           - CarbohydrateContent (g)
           - FiberContent (g)
           - SugarContent (g)
           - ProteinContent (g)
        4. Specify serving size per unit (e.g., 1 medium banana = 120g).
        Return the response in JSON format with fields: item_name, quantity, serving_size, nutrition_per_unit.
        Example:
        ```json
        [
            {
                "item_name": "Banana",
                "quantity": 5,
                "serving_size": "1 medium banana (120g)",
                "nutrition_per_unit": {
                    "Calories": 90,
                    "FatContent": 0.3,
                    "SaturatedFatContent": 0.1,
                    "CholesterolContent": 0,
                    "SodiumContent": 1,
                    "CarbohydrateContent": 23,
                    "FiberContent": 2.6,
                    "SugarContent": 12,
                    "ProteinContent": 1.1
                }
            }
        ]
        ```
        """
        response = model.generate_content([prompt, {"inline_data": {"data": img_byte_arr, "mime_type": "image/png"}}])
        import json
        try:
            result = json.loads(response.text.strip('```json\n').strip('```'))
        except json.JSONDecodeError:
            st.error("Failed to parse Gemini response. Please try again.", icon="❌")
            return []
        return result
    except Exception as e:
        st.error(f"Error analyzing image: {str(e)}", icon="❌")
        return []

def calculate_health_status(nutrition, quantity):
    """Determine health status and weight impact based on nutrition."""
    scaled_nutrition = {key: nutrition.get(key, 0) * quantity for key in nutrition_values}
    calories = scaled_nutrition['Calories']
    sugar = scaled_nutrition['SugarContent']
    fat = scaled_nutrition['FatContent']
    fiber = scaled_nutrition['FiberContent']
    
    if sugar < 25 and fat < 20 and calories < 500:
        health_status = "Healthy"
        health_color = "green"
    elif sugar < 50 and fat < 40 and calories < 1000:
        health_status = "Moderate"
        health_color = "yellow"
    else:
        health_status = "Unhealthy"
        health_color = "red"

    if calories < 300 and fiber > 5:
        weight_impact = "Supports Weight Loss"
    elif calories > 600:
        weight_impact = "Supports Weight Gain"
    else:
        weight_impact = "Supports Weight Maintenance"

    return health_status, health_color, weight_impact

class Display:
    def __init__(self):
        self.nutrition_values = nutrition_values
        self.plans = ["Maintain weight", "Mild weight loss", "Weight loss", "Extreme weight loss"]
        self.weights = [1, 0.9, 0.8, 0.6]
        self.losses = ['-0 kg/week', '-0.25 kg/week', '-0.5 kg/week', '-1 kg/week']

    def display_bmi(self, person):
        st.header('BMI CALCULATOR')
        bmi_string, category, color = person.display_result()
        st.metric(label="Body Mass Index (BMI)", value=bmi_string)
        new_title = f'<p style="font-family:sans-serif; color:{color}; font-size: 25px;">{category}</p>'
        st.markdown(new_title, unsafe_allow_html=True)
        st.markdown("Healthy BMI range: 18.5 kg/m² - 25 kg/m².")

    def display_calories(self, person):
        st.header('CALORIES CALCULATOR')
        maintain_calories = person.calories_calculator()
        st.write('The results show a number of daily calorie estimates that can be used as a guideline for how many calories to consume each day to maintain, lose, or gain weight at a chosen rate.')
        for plan, weight, loss, col in zip(self.plans, self.weights, self.losses, st.columns(4)):
            with col:
                st.metric(label=plan, value=f'{round(maintain_calories * weight)} Calories/day', delta=loss, delta_color="inverse")

    def display_diet_recommendation(self, person, recommendations):
        st.header('DIET RECOMMENDER')
        if recommendations:
            meals = person.meals_calories_perc
            st.subheader('Recommended recipes:')
            for meal_name, column, recommendation in zip(meals, st.columns(len(meals)), recommendations):
                with column:
                    st.markdown(f'##### {meal_name.upper()}')
                    for recipe in recommendation:
                        recipe_name = recipe.get('Name', 'Unknown Recipe')
                        expander = st.expander(recipe_name)
                        recipe_link = recipe.get('image_link', 'https://via.placeholder.com/200')
                        recipe_img = f'<div><center><img src="{recipe_link}" alt="{recipe_name}" width="200"></center></div>'
                        nutritions_df = pd.DataFrame({value: [recipe.get(value, 0)] for value in self.nutrition_values})

                        expander.markdown(recipe_img, unsafe_allow_html=True)
                        expander.markdown('<h5 style="text-align: center;font-family:sans-serif;">Nutritional Values (g):</h5>', unsafe_allow_html=True)
                        expander.dataframe(nutritions_df)
                        expander.markdown('<h5 style="text-align: center;font-family:sans-serif;">Ingredients:</h5>', unsafe_allow_html=True)
                        for ingredient in recipe.get('RecipeIngredientParts', []):
                            expander.markdown(f"- {ingredient}")
                        expander.markdown('<h5 style="text-align: center;font-family:sans-serif;">Recipe Instructions:</h5>', unsafe_allow_html=True)
                        for instruction in recipe.get('RecipeInstructions', []):
                            expander.markdown(f"- {instruction}")
                        expander.markdown('<h5 style="text-align: center;font-family:sans-serif;">Cooking and Preparation Time:</h5>', unsafe_allow_html=True)
                        expander.markdown(f"""
                            - Cook Time: {recipe.get('CookTime', 'N/A')}min
                            - Preparation Time: {recipe.get('PrepTime', 'N/A')}min
                            - Total Time: {recipe.get('TotalTime', 'N/A')}min
                        """)
        else:
            st.info('No recommendations available.', icon="🙁")

    def display_custom_recommendation(self, recommendations):
        st.subheader('Recommended recipes:')
        if recommendations:
            cols = 5
            num_recipes = len(recommendations)
            rows_needed = (num_recipes + cols - 1) // cols
            for row in range(rows_needed):
                columns = st.columns(cols)
                slice_start = row * cols
                slice_end = min(slice_start + cols, num_recipes)
                for col_idx, recipe in enumerate(recommendations[slice_start:slice_end]):
                    with columns[col_idx]:
                        recipe_name = recipe.get('Name', 'Unknown Recipe')
                        expander = st.expander(recipe_name)
                        recipe_link = recipe.get('image_link', 'https://via.placeholder.com/200')
                        recipe_img = f'<div><center><img src="{recipe_link}" alt="{recipe_name}" width="200"></center></div>'
                        nutritions_df = pd.DataFrame({value: [recipe.get(value, 0)] for value in self.nutrition_values})

                        expander.markdown(recipe_img, unsafe_allow_html=True)
                        expander.markdown('<h5 style="text-align: center;font-family:sans-serif;">Nutritional Values (g):</h5>', unsafe_allow_html=True)
                        expander.dataframe(nutritions_df)
                        expander.markdown('<h5 style="text-align: center;font-family:sans-serif;">Ingredients:</h5>', unsafe_allow_html=True)
                        for ingredient in recipe.get('RecipeIngredientParts', []):
                            expander.markdown(f"- {ingredient}")
                        expander.markdown('<h5 style="text-align: center;font-family:sans-serif;">Recipe Instructions:</h5>', unsafe_allow_html=True)
                        for instruction in recipe.get('RecipeInstructions', []):
                            expander.markdown(f"- {instruction}")
                        expander.markdown('<h5 style="text-align: center;font-family:sans-serif;">Cooking and Preparation Time:</h5>', unsafe_allow_html=True)
                        expander.markdown(f"""
                            - Cook Time: {recipe.get('CookTime', 'N/A')}min
                            - Preparation Time: {recipe.get('PrepTime', 'N/A')}min
                            - Total Time: {recipe.get('TotalTime', 'N/A')}min
                        """)
        else:
            st.info('Couldn\'t find any recipes with the specified ingredients', icon="🙁")

    def display_diet_meal_choices(self, person, recommendations):
        if recommendations:
            st.subheader('Choose your meal composition:')
            meals = list(person.meals_calories_perc.keys())
            choices = []
            columns = st.columns(len(meals))
            for idx, (meal_name, column, recommendation) in enumerate(zip(meals, columns, recommendations)):
                with column:
                    choice = st.selectbox(f'Choose your {meal_name}:', [recipe.get('Name', 'Unknown') for recipe in recommendation])
                    choices.append(choice)

            total_nutrition_values = {nutrition_value: 0 for nutrition_value in nutrition_values}
            for choice, meal_recommendations in zip(choices, recommendations):
                for meal in meal_recommendations:
                    if meal.get('Name') == choice:
                        for nutrition_value in nutrition_values:
                            total_nutrition_values[nutrition_value] += meal.get(nutrition_value, 0)

            total_calories_chose = total_nutrition_values['Calories']
            loss_calories_chose = round(person.calories_calculator() * person.weight_loss)

            st.markdown(f'<h5 style="text-align: center;font-family:sans-serif;">Total Calories in Recipes vs {st.session_state.weight_loss_option} Calories:</h5>', unsafe_allow_html=True)
            total_calories_graph_options = {
                "xAxis": {
                    "type": "category",
                    "data": ['Total Calories Chosen', f"{st.session_state.weight_loss_option} Calories"],
                },
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "data": [
                            {"value": total_calories_chose, "itemStyle": {"color": "#FF3333" if total_calories_chose > loss_calories_chose else "#33FF8D"}},
                            {"value": loss_calories_chose, "itemStyle": {"color": "#3339FF"}},
                        ],
                        "type": "bar",
                    }
                ],
            }
            st_echarts(options=total_calories_graph_options, height="400px")

            st.markdown(f'<h5 style="text-align: center;font-family:sans-serif;">Nutritional Values:</h5>', unsafe_allow_html=True)
            nutritions_graph_options = {
                "tooltip": {"trigger": "item"},
                "legend": {"top": "5%", "left": "center"},
                "series": [
                    {
                        "name": "Nutritional Values",
                        "type": "pie",
                        "radius": ["40%", "70%"],
                        "avoidLabelOverlap": False,
                        "itemStyle": {
                            "borderRadius": 10,
                            "borderColor": "#fff",
                            "borderWidth": 2,
                        },
                        "label": {"show": False, "position": "center"},
                        "emphasis": {
                            "label": {"show": True, "fontSize": "40", "fontWeight": "bold"}
                        },
                        "labelLine": {"show": False},
                        "data": [
                            {"value": round(total_nutrition_values[nutrition_value]), "name": nutrition_value}
                            for nutrition_value in nutrition_values
                        ],
                    }
                ],
            }
            st_echarts(options=nutritions_graph_options, height="500px")

    def display_custom_overview(self, recommendations):
        if recommendations:
            st.subheader('Overview:')
            col1, col2, col3 = st.columns(3)
            with col2:
                selected_recipe_name = st.selectbox('Select a recipe', [recipe.get('Name', 'Unknown') for recipe in recommendations])
            st.markdown('<h5 style="text-align: center;font-family:sans-serif;">Nutritional Values:</h5>', unsafe_allow_html=True)
            selected_recipe = next((recipe for recipe in recommendations if recipe.get('Name') == selected_recipe_name), None)
            if selected_recipe:
                options = {
                    "title": {"text": "Nutrition values", "subtext": f"{selected_recipe_name}", "left": "center"},
                    "tooltip": {"trigger": "item"},
                    "legend": {"orient": "vertical", "left": "left"},
                    "series": [
                        {
                            "name": "Nutrition values",
                            "type": "pie",
                            "radius": "50%",
                            "data": [{"value": selected_recipe.get(nutrition_value, 0), "name": nutrition_value} 
                                     for nutrition_value in self.nutrition_values],
                            "emphasis": {
                                "itemStyle": {
                                    "shadowBlur": 10,
                                    "shadowOffsetX": 0,
                                    "shadowColor": "rgba(0, 0, 0, 0.5)",
                                }
                            },
                        }
                    ],
                }
                st_echarts(options=options, height="600px")
            st.caption('You can select/deselect an item (nutrition value) from the legend.')

    def display_nutrition_analysis(self, analysis_result):
        """Display nutritional analysis in a single table per item with nutrient, per-unit, and total values."""
        if not analysis_result:
            st.info("No food items detected in the image.", icon="🙁")
            return

        st.subheader("Food Analysis")
        
        for item in analysis_result:
            item_name = item.get('item_name', 'Unknown')
            quantity = item.get('quantity', 1)
            serving_size = item.get('serving_size', 'N/A')
            nutrition_per_unit = item.get('nutrition_per_unit', {})

            total_nutrition = {key: nutrition_per_unit.get(key, 0) * quantity for key in nutrition_values}
            
            health_status, health_color, weight_impact = calculate_health_status(nutrition_per_unit, quantity)

            with st.expander(f"{item_name} (Quantity: {quantity})"):
                st.markdown(f"**Serving Size (per unit):** {serving_size}")
                st.markdown(f"**Health Status:** <span style='color:{health_color}'>{health_status}</span>", unsafe_allow_html=True)
                st.markdown(f"**Weight Impact:** {weight_impact}")

                st.markdown("**Nutrition Breakdown:**")
                nutrition_df = pd.DataFrame({
                    'Nutrient': nutrition_values,
                    'Per Unit (1)': [nutrition_per_unit.get(key, 0) for key in nutrition_values],
                    f'Total ({quantity} units)': [total_nutrition.get(key, 0) for key in nutrition_values]
                })
                st.table(nutrition_df.style.format({"Per Unit (1)": "{:.1f}", f"Total ({quantity} units)": "{:.1f}"}))

        total_nutrition_all = {key: 0 for key in nutrition_values}
        for item in analysis_result:
            quantity = item.get('quantity', 1)
            nutrition_per_unit = item.get('nutrition_per_unit', {})
            for key in nutrition_values:
                total_nutrition_all[key] += nutrition_per_unit.get(key, 0) * quantity

        st.subheader("Total Nutrition (All Items)")
        health_status, health_color, weight_impact = calculate_health_status(total_nutrition_all, 1)
        st.markdown(f"**Overall Health Status:** <span style='color:{health_color}'>{health_status}</span>", unsafe_allow_html=True)
        st.markdown(f"**Overall Weight Impact:** {weight_impact}")
        total_nutrition_df = pd.DataFrame({
            'Nutrient': nutrition_values,
            'Total Value': [total_nutrition_all.get(key, 0) for key in nutrition_values]
        })
        st.table(total_nutrition_df.style.format({"Total Value": "{:.1f}"}))

# Main app
display = Display()
st.markdown("<h1 style='text-align: center;'>Diet & Food Recommendation</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Diet Recommendation", "Custom Food Recommendation", "Food Nutrition Analyzer"])

# Diet Recommendation Tab
with tab1:
    with st.form("diet_recommendation_form"):
        st.write("Modify the values and click the Generate button to use")
        age = st.number_input('Age', min_value=2, max_value=120, step=1)
        height = st.number_input('Height(cm)', min_value=50, max_value=300, step=1)
        weight = st.number_input('Weight(kg)', min_value=10, max_value=300, step=1)
        gender = st.radio('Gender', ('Male', 'Female'))
        foodType = st.radio('Food Type', ('Veg', 'Non-Veg'))
        activity = st.select_slider('Activity', options=['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)', 
                                                        'Very active (6-7 days/wk)', 'Extra active (very active & physical job)'])
        option = st.selectbox('Choose your weight loss plan:', display.plans)
        st.session_state.weight_loss_option = option
        weight_loss = display.weights[display.plans.index(option)]
        number_of_meals = st.slider('Meals per day', min_value=3, max_value=5, step=1, value=3)
        if number_of_meals == 3:
            meals_calories_perc = {'breakfast': 0.35, 'lunch': 0.40, 'dinner': 0.25}
        elif number_of_meals == 4:
            meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'dinner': 0.25}
        else:
            meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'afternoon snack': 0.05, 'dinner': 0.20}
        diet_generated = st.form_submit_button("Generate")

    if diet_generated:
        st.session_state.diet_generated = True
        person = Person(age, height, weight, gender, foodType, activity, meals_calories_perc, weight_loss)
        st.session_state.person = person
        with st.container():
            display.display_bmi(person)
        with st.container():
            display.display_calories(person)
        with st.spinner('Generating recommendations...'):
            recommendations = person.generate_recommendations()
            st.session_state.diet_recommendations = recommendations

    if st.session_state.diet_generated and st.session_state.person and st.session_state.diet_recommendations:
        with st.container():
            display.display_diet_recommendation(st.session_state.person, st.session_state.diet_recommendations)
            st.success('Diet Recommendations Generated Successfully!', icon="✅")
        with st.container():
            display.display_diet_meal_choices(st.session_state.person, st.session_state.diet_recommendations)

# Custom Food Recommendation Tab
with tab2:
    with st.form("custom_recommendation_form"):
        st.header('Nutritional values:')
        Calories = st.slider('Calories', 0, 2000, 500)
        FatContent = st.slider('FatContent', 0, 100, 50)
        SaturatedFatContent = st.slider('SaturatedFatContent', 0, 13, 0)
        CholesterolContent = st.slider('CholesterolContent', 0, 300, 0)
        SodiumContent = st.slider('SodiumContent', 0, 2300, 400)
        CarbohydrateContent = st.slider('CarbohydrateContent', 0, 325, 100)
        FiberContent = st.slider('FiberContent', 0, 50, 10)
        SugarContent = st.slider('SugarContent', 0, 40, 10)
        ProteinContent = st.slider('ProteinContent', 0, 40, 10)
        nutritions_values_list = [Calories, FatContent, SaturatedFatContent, CholesterolContent, SodiumContent, 
                                  CarbohydrateContent, FiberContent, SugarContent, ProteinContent]
        
        st.header('Recommendation options (OPTIONAL):')
        nb_recommendations = st.slider('Number of recommendations', 5, 20, step=5)
        ingredient_txt = st.text_input('Ingredients (separated by ;)', '', help='Example: Milk;eggs;butter;chicken...')
        
        custom_generated = st.form_submit_button("Generate")

    if custom_generated:
        with st.spinner('Generating recommendations...'):
            recommendation = Recommendation(nutritions_values_list, nb_recommendations, ingredient_txt)
            recommendations = recommendation.generate()
            st.session_state.custom_recommendations = recommendations
        st.session_state.custom_generated = True

    if st.session_state.custom_generated and st.session_state.custom_recommendations:
        with st.container():
            display.display_custom_recommendation(st.session_state.custom_recommendations)
            st.success('Custom Recommendations Generated Successfully!', icon="✅")
        with st.container():
            display.display_custom_overview(st.session_state.custom_recommendations)

# Food Nutrition Analyzer Tab
with tab3:
    st.write("Upload an image of food to analyze its nutritional content. The app will detect food items, their quantities, and provide detailed nutrition information.")
    uploaded_file = st.file_uploader("Choose a food image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.session_state.uploaded_image = image
        st.image(image, caption="Uploaded Food Image", use_column_width=True)

        if st.button("Analyze Food"):
            with st.spinner("Analyzing image..."):
                st.session_state.analysis_result = analyze_food_image(image)
            st.success("Analysis Complete!", icon="✅")

    if st.session_state.analysis_result:
        display.display_nutrition_analysis(st.session_state.analysis_result)
