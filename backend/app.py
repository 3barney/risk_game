from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import Literal, List

from risk_feature import compute_risk

app = FastAPI(title="Risk Games for Credit API")


class SingleShotQuestion(BaseModel):
    game: Literal["single"]
    choice: Literal["safe", "risky"]

class MultiShotQuestion(BaseModel):
    game: Literal["multiple"]
    choices: Literal[Literal["safe", "risky"]] = Field(min_items=4, max_items=4)

class SliderQuestion(BaseModel):
    game: Literal["slider"]
    certainty: float = Field(ge=0, le=100)

class BallonQuestion(BaseModel):
    game: Literal["ballon"]
    pumps: int = Field(ge=0)
    popped: bool

class BudgetQuestion(BaseModel):
    game: Literal["budget"]
    risk_tokens: int = Field(ge=0, le=100)

AnyGame = SingleShotQuestion, MultiShotQuestion, SliderQuestion, BallonQuestion, BudgetQuestion

in_memory_datastore: list[dict] = []

@app.post("/game_data")
async def create_game(game: AnyGame):
    risk = compute_risk(game.model_dump())
    in_memory_datastore.append({"id": str(uuid4()), "game": game.game, "risk": risk})
    return {"risk_score": risk}

