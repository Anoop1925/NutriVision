from main import update_item
from main import PredictionIn, ParamsModel  # Importing these from main

# class Generator:
#     def __init__(self, nutrition_input: list, ingredients: list = [], ParamsModel: dict = {'n_neighbors': 5, 'return_distance': False}):
#         self.nutrition_input = nutrition_input
#         self.ingredients = ingredients
#         self.params = ParamsModel
#         self.food_type = food_type

#     def set_request(self, nutrition_input: list, ingredients: list, ParamsModel: dict):
#         self.nutrition_input = nutrition_input
#         self.ingredients = ingredients
#         self.params = ParamsModel

#     def generate(self):
#         # Creating the PredictionIn object using the provided params
#         prediction_input = PredictionIn(
#             nutrition_input=self.nutrition_input,
#             ingredients=self.ingredients,
#             params=ParamsModel(**self.params)  # Convert params dictionary to params object
#         )
#         # Call update_item with the newly created PredictionIn object
#         response = update_item(prediction_input)
#         return response

class Generator:
    def __init__(self, nutrition_input: list, ingredients: list = [], ParamsModel: dict = {'n_neighbors': 5, 'return_distance': False}, food_type: str = None):
        self.nutrition_input = nutrition_input
        self.ingredients = ingredients
        self.params = ParamsModel
        self.food_type = food_type

    def set_request(self, nutrition_input: list, ingredients: list, ParamsModel: dict, food_type: str):
        self.nutrition_input = nutrition_input
        self.ingredients = ingredients
        self.params = ParamsModel
        self.food_type = food_type

    def generate(self):
        # Creating the PredictionIn object using the provided params
        prediction_input = PredictionIn(
            nutrition_input=self.nutrition_input,
            ingredients=self.ingredients,
            params=ParamsModel(**self.params),  # Convert params dictionary to params object
            food_type=self.food_type  # Pass the food type
        )
        # Call update_item with the newly created PredictionIn object
        response = update_item(prediction_input)
        return response