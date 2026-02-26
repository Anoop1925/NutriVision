import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

st.set_page_config(page_title="Food Nutrition Analyzer", page_icon="🍽️", layout="wide")

# Configure Gemini API
API_KEY = "AIzaSyCgRNgd04AllhAdKTdbDFNlG-ollnwsTTI"
genai.configure(api_key=API_KEY)
# Note: Using gemini-1.5-flash as it's the latest vision model (Sep 2025). Change to gemini-2.5-flash if you have specific access.
model = genai.GenerativeModel('gemini-2.5-flash')

# Nutrition values to display
nutrition_values = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent', 'SodiumContent', 
                    'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
    st.session_state.uploaded_image = None

def analyze_food_image(image):
    """Analyze the uploaded image using Gemini to detect food items and quantities."""
    try:
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Prompt for Gemini to identify food items, quantities, and nutrition
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
        # Parse JSON response
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
    # Scale nutrition by quantity for evaluation
    scaled_nutrition = {key: nutrition.get(key, 0) * quantity for key in nutrition_values}
    
    # Health status: Based on sugar, fat, and calorie thresholds
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

    # Weight impact: Based on calorie density and fiber
    if calories < 300 and fiber > 5:
        weight_impact = "Supports Weight Loss"
    elif calories > 600:
        weight_impact = "Supports Weight Gain"
    else:
        weight_impact = "Supports Weight Maintenance"

    return health_status, health_color, weight_impact

def display_nutrition(analysis_result):
    """Display nutritional analysis in a single table per item with nutrient, per-unit, and total values."""
    if not analysis_result:
        st.info("No food items detected in the image.", icon="🙁")
        return

    st.subheader("Food Analysis")
    
    # Display individual items
    for item in analysis_result:
        item_name = item.get('item_name', 'Unknown')
        quantity = item.get('quantity', 1)
        serving_size = item.get('serving_size', 'N/A')
        nutrition_per_unit = item.get('nutrition_per_unit', {})

        # Calculate total nutrition
        total_nutrition = {key: nutrition_per_unit.get(key, 0) * quantity for key in nutrition_values}
        
        # Determine health status and weight impact
        health_status, health_color, weight_impact = calculate_health_status(nutrition_per_unit, quantity)

        # Display item details
        with st.expander(f"{item_name} (Quantity: {quantity})"):
            st.markdown(f"**Serving Size (per unit):** {serving_size}")
            st.markdown(f"**Health Status:** <span style='color:{health_color}'>{health_status}</span>", unsafe_allow_html=True)
            st.markdown(f"**Weight Impact:** {weight_impact}")

            # Combined nutrition table
            st.markdown("**Nutrition Breakdown:**")
            nutrition_df = pd.DataFrame({
                'Nutrient': nutrition_values,
                'Per Unit (1)': [nutrition_per_unit.get(key, 0) for key in nutrition_values],
                f'Total ({quantity} units)': [total_nutrition.get(key, 0) for key in nutrition_values]
            })
            st.table(nutrition_df.style.format({"Per Unit (1)": "{:.1f}", f"Total ({quantity} units)": "{:.1f}"}))

    # Total nutrition across all items
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
st.markdown("<h1 style='text-align: center;'>Food Nutrition Analyzer</h1>", unsafe_allow_html=True)
st.write("Upload an image of food to analyze its nutritional content. The app will detect food items, their quantities, and provide detailed nutrition information.")

# Image upload
uploaded_file = st.file_uploader("Choose a food image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Display uploaded image
    image = Image.open(uploaded_file)
    st.session_state.uploaded_image = image
    st.image(image, caption="Uploaded Food Image", use_column_width=True)

    # Analyze button
    if st.button("Analyze Food"):
        with st.spinner("Analyzing image..."):
            st.session_state.analysis_result = analyze_food_image(image)
        st.success("Analysis Complete!", icon="✅")

# Display results
if st.session_state.analysis_result:
    display_nutrition(st.session_state.analysis_result)
