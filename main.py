from pydantic import BaseModel, conlist
from typing import List, Optional
from model import recommend, output_recommended_recipes

# Lazy-load the dataset — avoids blocking worker boot on Railway
_dataset = None

def get_dataset():
    global _dataset
    if _dataset is None:
        import pandas as pd
        _dataset = pd.read_csv('updated.csv')
    return _dataset

# Define the params model
class ParamsModel(BaseModel):
    n_neighbors: int = 5
    return_distance: bool = False

# Define the PredictionIn model
class PredictionIn(BaseModel):
    nutrition_input: conlist(float)
    ingredients: List[str] = []
    params: Optional[ParamsModel] = None
    food_type: Optional[str] = None


class Recipe(BaseModel):
    Name: str
    CookTime: str
    PrepTime: str
    TotalTime: str
    RecipeIngredientParts: List[str]
    Calories: float
    FatContent: float
    SaturatedFatContent: float
    CholesterolContent: float
    SodiumContent: float
    CarbohydrateContent: float
    FiberContent: float
    SugarContent: float
    ProteinContent: float
    RecipeInstructions: List[str]
    FoodType: str

# Define the PredictionOut model
class PredictionOut(BaseModel):
    output: Optional[List[Recipe]] = None

# Update item function that takes PredictionIn as input
# def update_item(prediction_input: PredictionIn):
#     recommendation_dataframe = recommend(
#         dataset,
#         prediction_input.nutrition_input,
#         prediction_input.ingredients,
#         prediction_input.params.dict() if prediction_input.params else {}
#     )
#     output = output_recommended_recipes(recommendation_dataframe)
    
#     return {"output": output if output is not None else None}


def update_item(prediction_input: PredictionIn):
    recommendation_dataframe = recommend(
        get_dataset(),
        prediction_input.nutrition_input,
        prediction_input.ingredients,
        prediction_input.params.dict() if prediction_input.params else {},
        food_type=prediction_input.food_type  # Pass the food type to the recommend function
    )
    output = output_recommended_recipes(recommendation_dataframe)
    
    return {"output": output if output is not None else None}