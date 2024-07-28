from fastapi import APIRouter

from ..config import settings
from ..game import GameSystem, GameSession, Prompt

router = APIRouter()
system = GameSystem()

@router.get("/new")
def new_game() -> GameSession:
    return system.new_game()

@router.get("/genlevel/{sessionid}")
def generate_level(sessionid: str) -> GameSession:
    # TODO: Get random repository ID
    repo_id = "WongNung/WongNung"   # example repo
    level = system.generate_new_level(sessionid, repo_id)
    system.generate_new_prompt(sessionid, level)
    return system.get_session(sessionid)

@router.get("/submit/{sessionid}/yes")
def submit_yes(sessionid: str) -> GameSession:
    return system.send_answer(sessionid, True)

@router.get("/submit/{sessionid}/no")
def submit_yes(sessionid: str) -> GameSession:
    return system.send_answer(sessionid, False)
