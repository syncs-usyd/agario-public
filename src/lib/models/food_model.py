from pydantic import BaseModel


class FoodModel(BaseModel):
    food_id: int
    pos: tuple[float, float]
