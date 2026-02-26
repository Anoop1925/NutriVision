"""
Custom recommendation service — wraps the Generator for free-form nutritional search.
"""
from GenerateRecommendations import Generator
from ImageFind import get_images_links as find_image


def generate_custom_recommendations(nutrition_input, nb_recommendations, ingredient_txt):
    params = {'n_neighbors': nb_recommendations, 'return_distance': False}
    ingredients = ingredient_txt.split(';') if ingredient_txt else []
    gen = Generator(nutrition_input, ingredients, params)
    recipes = gen.generate()['output']
    if recipes:
        for r in recipes:
            r['image_link'] = find_image(r.get('Name', ''))
    return recipes or []
