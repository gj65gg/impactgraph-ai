
import hmac
import re

from fastapi import (
    FastAPI,
    Header,
    HTTPException
)

from pydantic import BaseModel, Field

from app.config import setting
from app.agent import analyze_impact
from app.graph import DependencyGraph


app = FastAPI(
    title="ImpactGraph AI",
    version="0.1.0"
)


class AnalyzeRequest(BaseModel):
    sys_id: str

    proposed_script: str | None = Field(
        default=None,
        max_length=25000
    )


def authorize(key):
    expected = setting("APP_API_KEY")

    if not hmac.compare_digest(
        key or "",
        expected
    ):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )


def validate(sys_id):
    if not re.fullmatch(
        r"[a-fA-F0-9]{32}",
        sys_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid sys_id"
        )


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/impact/{sys_id}")
def impact(
    sys_id: str,
    x_api_key: str = Header(default="")
):
    authorize(x_api_key)
    validate(sys_id)

    graph = DependencyGraph()

    try:
        return {
            "sys_id": sys_id,
            "candidate_dependents":
                graph.get_impact(sys_id),
            "coverage": (
                "Constructor-based "
                "dependencies only"
            )
        }
    finally:
        graph.close()


@app.post("/analyze")
async def analyze(
    request: AnalyzeRequest,
    x_api_key: str = Header(default="")
):
    authorize(x_api_key)
    validate(request.sys_id)

    result = await analyze_impact(
        request.sys_id,
        request.proposed_script
    )

    return {
        "sys_id": request.sys_id,
        "analysis": result
    }
