from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .. import models, schemas


def create_lead(db: Session, lead_data: schemas.LeadCreate) -> models.Lead:
    """
    Erstellt einen neuen Lead in der Datenbank.
    Optional kann dabei auch ein Primärkontakt (mit E-Mail-Adressen) direkt mit angelegt werden.
    """

    # Neuen Lead aus den übergebenen Daten erzeugen
    lead = models.Lead(
        name=lead_data.name,
        domain=lead_data.domain,
        status=lead_data.status or models.LeadStatus.new,
    )
    db.add(lead)
    db.flush()

    # Prüfen, ob ein Primärkontakt mitgeschickt wurde
    if lead_data.primary_contact:
        contact_data = lead_data.primary_contact
        contact = models.Contact(
            first_name=contact_data.first_name,
            last_name=contact_data.last_name
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


def get_leads(db: Session,
              q: Optional[str],
              status: Optional[str],
              limit: int,
              offset: int) -> Tuple[List[models.Lead], int]:
    """
    Holt Leads aus der Datenbank mit optionaler Filterung nach Status und Suchtext.
    Unterstützt Pagination über limit/offset.
    Gibt sowohl die Ergebnisliste als auch die Gesamtanzahl zurück.
    """
    
    query = select(models.Lead)
    count_query = select(func.count()).select_from(models.Lead)

    # Optionaler Filter: nach Status (z. B. "new", "qualified", "lost")
    if status:
        query = query.where(models.Lead.status == status)
        count_query = count_query.where(models.Lead.status == status)

    # Optionaler Filter: Textsuche über name oder domain (case-insensitive)
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

    # Gesamtanzahl aller Treffer (für Pagination)
    total = db.execute(count_query).scalar_one()

    # Sortierung: neueste Leads zuerst
    query = query.order_by(models.Lead.created_at.desc()).limit(limit).offset(offset)

    # Ausführen der eigentlichen Query → Liste der Leads
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
    db.add(lead)
    db.flush()
    return lead
