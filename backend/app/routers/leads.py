from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from ..database import SessionLocal
from .. import schemas, models, crud
import logging

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/leads", tags=["leads"])


def get_db():
    """
    Dependency-Funktion für FastAPI.
    Erstellt eine neue Datenbank-Session pro Request und schließt sie am Ende wieder.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=schemas.LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(lead_data: schemas.LeadCreate, db: Session = Depends(get_db)):
    """
    POST /leads
    Erstellt einen neuen Lead (optional mit Primärkontakt und E-Mail).
    Rückgabe: Der erstellte Lead als Schema (LeadRead).
    """

    logger.info("create_lead() called")
    logger.debug(f"Lead received: {lead_data.model_dump()}")
    
    try:
        with db.begin():
            lead = crud.create_lead(db, lead_data)
            db.refresh(lead)
            logger.info(f"Lead created successfully: ID={lead.id}")
            return lead
    except ValueError as e:
        logger.exception(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error in create_lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=schemas.LeadsList)
def get_leads(
    q: Optional[str] = Query(None),
    status: Optional[models.LeadStatus] = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    GET /leads
    Liefert eine Liste aller Leads mit optionalen Filtern (Suche, Status).
    Unterstützt Pagination (limit/offset).
    """

    logger.info(f"get_leads(q={q}, status={status}, limit={limit}, offset={offset})")
    leads, total = crud.get_leads(db, q=q, status=status, limit=limit, offset=offset)
    logger.info(f"get_leads returned {len(leads)} leads (total={total})")
    
    return {"items": leads, "total": total}


@router.post("/{lead_id}/status", response_model=schemas.LeadRead)
def set_lead_status(lead_id: int, new_status: models.LeadStatus, db: Session = Depends(get_db)):
    """
    POST /leads/{lead_id}/status
    Aktualisiert den Status eines Leads.
    """

    logger.info(f"set_status(lead_id={lead_id}, new_status={new_status})")
    with db.begin():
        lead = crud.update_lead_status(db, lead_id, new_status)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        db.refresh(lead)
        logger.info(f"Status updated for lead {lead_id}")
        return lead
