import pandas as pd
import ast

df = pd.read_csv('dataset.csv')

def split_ingredients(ingredients_list):
    split_list = []
    for ingredient in ingredients_list:
        # Split each ingredient into words
        words = ingredient.split()
        split_list.extend(words)  # Add the words to the final list
    return split_list

def vegNon(ingredients):
    non_veg_keywords = [
    # Common Meats
    'chicken', 'beef', 'pork', 'lamb', 'mutton', 'turkey', 'duck', 'rabbit', 'venison', 
    'bison', 'goat', 'quail', 'pheasant', 'kangaroo', 'wild boar', 'ostrich', 'frog legs',

    # Seafood
    'fish', 'shrimp', 'prawn', 'crab', 'lobster', 'oyster', 'clam', 'mussel', 'scallop', 
    'squid', 'octopus', 'anchovy', 'sardine', 'tuna', 'salmon', 'trout', 'cod', 'mackerel',
    'haddock', 'eel', 'caviar', 'roe', 'shark', 'stingray', 'snapper', 'barramundi', 'catfish', 
    'halibut', 'swordfish', 'bass', 'perch', 'grouper', 'flounder', 'pollock', 'herring',

    # Processed Meats
    'bacon', 'sausage', 'pepperoni', 'salami', 'ham', 'pastrami', 'prosciutto', 'mortadella', 
    'bologna', 'chorizo', 'spam', 'jerky', 'hot dog', 'cold cuts', 'deli meat', 'pâté',

    # Broths & Sauces
    'bone broth', 'stock', 'chicken stock', 'beef stock', 'pork stock', 'fish stock', 'shrimp stock', 
    'meat broth', 'gelatin', 'lard', 'tallow', 'schmaltz', 'fish sauce', 'oyster sauce', 'clam juice', 
    'shrimp paste', 'anchovy paste', 'Worcestershire sauce (contains anchovies)',

    # Animal By-products
    'egg', 'fish eggs', 'roe', 'caviar', 'rennet (from animals)', 'suet', 'ghee (if not plant-based)',
    'gravy (if made from meat drippings)', 'marrow', 'head cheese',

    # Exotic Meats & Others
    'alligator', 'crocodile', 'snake', 'snail', 'turtle', 'insects', 'silkworm', 'grasshopper', 
    'crickets', 'scorpions', 'tarantula', 'blood pudding', 'black pudding', 'haggis', 'sweetbreads', 
    'tripe', 'offal', 'liver', 'kidney', 'heart', 'tongue', 'brain', 'gizzard', 'duck liver', 'foie gras'
]

    
    cleaned_string = ingredients.strip('[]') 
    cleaned_string = cleaned_string.replace('"', "'")  

    
    try:
        ingredients_list = ast.literal_eval(cleaned_string)
    except (SyntaxError, ValueError):
        ingredients_list = [ingredient.strip() for ingredient in cleaned_string.strip('[]').split(',')]
    
    ingredients_list = split_ingredients(ingredients_list)
    for i in non_veg_keywords:
        if i in ingredients_list:
            return "Non-Veg"
    return "Veg"

df['FoodType'] = df['RecipeIngredientParts'].apply(vegNon)

df.to_csv('updated_dataset.csv', index=False)

print(df.head())