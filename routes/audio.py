"""
routes/audio.py — Audio processing endpoint.

POST /process-audio/  →  AudioReportResponse JSON  +  DOCX download link
"""
import traceback
from fastapi            import APIRouter, UploadFile, File, HTTPException
from fastapi.responses  import JSONResponse
from models.report_schema import AudioReportResponse, ErrorResponse
from services.main_service import process_audio_to_report

router = APIRouter(tags=["Audio Report"])


@router.post(
    "/process-audio/",
    response_model=AudioReportResponse,
    summary="Upload audio → get structured report + DOCX",
    # responses={500: {"model": ErrorResponse}}
)
async def process_audio(file: UploadFile = File(...)):
    try:
        result = await process_audio_to_report(file)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "trace": traceback.format_exc()
            }
        )