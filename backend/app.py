from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conlist
from typing import Literal, List, Union, Annotated
from uuid import uuid4
import logging

from risk_feature import compute_risk

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Risk Games for Credit API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SingleShotQuestion(BaseModel):
    game: Literal["single"]
    choice: Literal["safe", "risky"]

class MultiShotQuestion(BaseModel):
    game: Literal["multiple"]
    choices: List[Literal["safe", "risky"]] = Field(..., min_items=4, max_items=4)

class SliderQuestion(BaseModel):
    game: Literal["slider"]
    certainty: float = Field(..., ge=0, le=100)

class BalloonQuestion(BaseModel):
    game: Literal["balloon"]
    pumps: int = Field(..., ge=0)
    popped: bool

class BudgetQuestion(BaseModel):
    game: Literal["budget"]
    risky_tokens: int = Field(..., ge=0, le=100)

class RiskGameQuestion(BaseModel):
    game: Literal["risk"]
    choices: conlist(Literal["safe", "risky"], min_length=1, max_length=10)

AnyGame = Annotated[
    Union[
        SingleShotQuestion,
        MultiShotQuestion,
        SliderQuestion,
        BalloonQuestion,
        BudgetQuestion,
        RiskGameQuestion,
    ],
    Field(discriminator="game"),
]


_data: list[dict] = []

@app.post("/game_data")
async def create_game(payload: AnyGame):
    logger.info(f"Received payload: {payload}")
    try:
        risk = compute_risk(payload.model_dump())
        _data.append(
            {
                "id": str(uuid4()),
                "game": payload.game,
                "risk": risk,
            }
        )
        logger.info(f"Created game: {payload.game} with risk score: {risk}")
        return {"risk_score": risk}
    except ValueError as e:
        logger.error(f"ValueError in compute_risk: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing game data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")