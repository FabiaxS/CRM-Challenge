from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .. import models, schemas


def create_lead(db: Session, lead_data: schemas.LeadCreate, tenant_id: str) -> models.Lead:
    """
    Erstellt einen neuen Lead in der Datenbank.
    Optional kann dabei auch ein Primärkontakt (mit E-Mail-Adressen) direkt mit angelegt werden.
    """

    # Neuen Lead aus den übergebenen Daten erzeugen
    lead = models.Lead(
        name=lead_data.name,
        domain=lead_data.domain,
        status=lead_data.status or models.LeadStatus.new,
        company_size=lead_data.company_size,
        industry=lead_data.industry,
        last_contacted=lead_data.last_contacted,
        tenant_id=tenant_id,
    )
    lead.priority = calculate_priority(lead)
    db.add(lead)
    db.flush()

    # Prüfen, ob ein Primärkontakt mitgeschickt wurde
    if lead_data.primary_contact:
        contact_data = lead_data.primary_contact
        contact = models.Contact(
            first_name=contact_data.first_name,
            last_name=contact_data.last_name,
            tenant_id=tenant_id,
        )
        db.add(contact)
        db.flush()

        # Vorbereitung für E-Mail-Prüfung
        seen_emails = set() # Hilfsmenge, um doppelte E-Mail-Adressen zu erkennen
        primary_email_set = False # Flag, um zu prüfen, ob eine Primary-Mail gesetzt wurde
        emails_objects = []

        # Wenn E-Mail-Adressen übergeben wurden:
        if contact_data.emails:
            for email in contact_data.emails:

                # Sicherstellen, dass eine E-Mail-Adresse pro Kontakt nur einmal vorkommt
                email_lower = email.value.strip().lower()
                if email_lower in seen_emails:
                    raise ValueError(f"Duplicate email for contact: {email.value}")
                seen_emails.add(email_lower)

                email_object = models.ContactEmail(
                    contact_id=contact.id,
                    value=email.value.strip(),
                    is_primary=bool(email.is_primary)
                )
                emails_objects.append(email_object)

                # Prüfen, ob mindestens eine E-Mail als "primary" markiert wurde
                if email.is_primary:
                    primary_set = True

        # Falls keine Primary-Mail angegeben wurde → erste Mail als Primary verwenden
        if emails_objects and not primary_email_set:
            emails_objects[0].is_primary = True

        for em in emails_objects:
            db.add(email_object)

        db.flush()

        # Primärkontakt dem Lead zuweisen
        lead.primary_contact_id = contact.id

    db.flush()
    return lead

def calculate_priority(lead: models.Lead) -> int:
    """
    Priorität eines Leads anhand verschiedener Faktoren berechnen.
    """
    score = 0

    # Status
    if lead.status == models.LeadStatus.new:
        score += 10
    elif lead.status == models.LeadStatus.qualified:
        score += 50
    elif lead.status == models.LeadStatus.lost:
        score += 0

    # Primärkontakt
    if lead.primary_contact:
        score += 20

    # Domain vorhanden
    if lead.domain:
        score += 10

    # Unternehmensgröße
    if lead.company_size:
        if lead.company_size < 50:
            score += 10
        elif lead.company_size < 200:
            score += 20
        else:
            score += 30

    # Branche
    if lead.industry:
        high_priority_industries = ["Tech", "Finanzen", "Healthcare"]
        if lead.industry in high_priority_industries:
            score += 15

    # Letzte Aktivität (z. B. Kontaktaufnahme)
    if lead.last_contacted:
        days_since = (datetime.utcnow() - lead.last_contacted).days
        if days_since < 7:
            score += 20
        elif days_since < 30:
            score += 10
        else:
            score += 0
    return score


def get_leads(db: Session,
              tenant_id: str,
              q: Optional[str],
              status: Optional[str],
              limit: int,
              offset: int) -> Tuple[List[models.Lead], int]:
    """
    Holt Leads aus der Datenbank mit optionaler Filterung nach Status und Suchtext.
    Jetzt inkl. Sortierung nach priority DESC zuerst.
    """
    
    query = select(models.Lead).where(models.Lead.tenant_id == tenant_id)
    count_query = select(func.count()).select_from(models.Lead).where(models.Lead.tenant_id == tenant_id)

    if status:
        query = query.where(models.Lead.status == status)
        count_query = count_query.where(models.Lead.status == status)

    if q:
        q_pattern_low = f"%{q.strip().lower()}%"
        query = query.where(
            func.lower(models.Lead.name).like(q_pattern_low) |
            func.lower(models.Lead.domain).like(q_pattern_low)
        )
        count_query = count_query.where(
            func.lower(models.Lead.name).like(q_pattern_low) |
            func.lower(models.Lead.domain).like(q_pattern_low)
        )

    total = db.execute(count_query).scalar_one()

    # Reihenfolge: priority DESC, dann neueste zuerst
    query = query.order_by(models.Lead.priority.desc(), models.Lead.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    leads = db.execute(query).scalars().all()
    return leads, total


def update_lead_status(db: Session, lead_id: int, new_status: str) -> Optional[models.Lead]:
    """
    Aktualisiert den Status eines Leads.
    Gibt den aktualisierten Lead zurück, oder None, falls keine ID gefunden wurde.
    """

    # Lead mit der angegebenen ID aus der Datenbank holen
    lead = db.execute(select(models.Lead).where(models.Lead.id == lead_id)).scalar_one_or_none()
    if not lead:
        return None

    # Status aktualisieren und speichern
    lead.status = new_status
    lead.priority = calculate_priority(lead)
    db.add(lead)
    db.flush()
    return lead
