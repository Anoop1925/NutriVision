import streamlit as st
import pandas as pd
from GenerateRecommendations import Generator
from random import uniform as rnd
from ImageFind import get_images_links as find_image
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Diet Recommendation", page_icon="💪", layout="wide")

nutrition_values = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent', 'SodiumContent', 
                    'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']

if 'person' not in st.session_state:
    st.session_state.generated = False
    st.session_state.recommendations = None
    st.session_state.person = None
    st.session_state.weight_loss_option = None

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

class Display:
    def __init__(self):
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

    def display_recommendation(self, person, recommendations):
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
                        recipe_link = recipe.get('image_link', '')
                        recipe_img = f'<div><center><img src="{recipe_link}" alt="{recipe_name}" width="200"></center></div>'
                        nutritions_df = pd.DataFrame({value: [recipe.get(value, 0)] for value in nutrition_values})

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

    def display_meal_choices(self, person, recommendations):
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

display = Display()
title = "<h1 style='text-align: center;'>Diet Recommendation</h1>"
st.markdown(title, unsafe_allow_html=True)

with st.form("recommendation_form"):
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
    generated = st.form_submit_button("Generate")

if generated:
    st.session_state.generated = True
    person = Person(age, height, weight, gender, foodType, activity, meals_calories_perc, weight_loss)
    st.session_state.person = person
    with st.container():
        display.display_bmi(person)
    with st.container():
        display.display_calories(person)
    with st.spinner('Generating recommendations...'):
        recommendations = person.generate_recommendations()
        st.session_state.recommendations = recommendations

if st.session_state.generated and st.session_state.person and st.session_state.recommendations:
    with st.container():
        display.display_recommendation(st.session_state.person, st.session_state.recommendations)
        st.success('Recommendation Generated Successfully!', icon="✅")
    with st.container():
        display.display_meal_choices(st.session_state.person, st.session_state.recommendations)