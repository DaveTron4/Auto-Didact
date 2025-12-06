from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.services import llm_engine
from app.services import media_engine

router = APIRouter()


class SceneModel(BaseModel):
    id: Optional[int]
    narrator_text: str
    image_prompt: str


class ScriptModel(BaseModel):
    title: Optional[str]
    scenes: List[SceneModel]


class VideoRequest(BaseModel):
    # Either provide a pre-built script or provide `context` to generate one
    script: Optional[ScriptModel] = None
    context: Optional[str] = None
    title: Optional[str] = "Auto-Didact Video"


@router.post("/generate-video")
async def generate_video(request: VideoRequest):
    """Generate a video from a provided script or from context using the LLM + media engine."""
    if request.script is None and not request.context:
        raise HTTPException(status_code=400, detail="Provide either 'script' or 'context'.")

    # Obtain script
    if request.script is not None:
        script = request.script.dict()
    else:
        # Generate script from context
        try:
            script = llm_engine.generate_script(request.context, title=request.title)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Script generation failed: {e}")

    # Create video
    try:
        output_path = await media_engine.create_video_from_script(script)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Media generation failed: {e}")

    return {"status": "success", "video_path": output_path}
