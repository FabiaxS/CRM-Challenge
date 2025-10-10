import React from "react";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createLead } from "../api/client";

// Validierung einzelner E-Mail-Einträge
const ContactEmailSchema = z.object({
  value: z.string().min(1, "Email darf nicht leer sein").email("Ungültige Email"),
  is_primary: z.boolean().optional().default(false),
});

// Validierung eines Kontakts
const ContactSchema = z.object({
  first_name: z.string().optional().nullable(),
  last_name: z.string().optional().nullable(),
  emails: z
    .array(ContactEmailSchema)
    .min(1, "Mindestens eine Email erforderlich")
    .refine(
      (emails) => emails.filter((e) => e.is_primary).length === 1,
      "Es muss genau eine Primary-Email geben"
    ),
});

// Hauptschema für Lead-Validierung
const LeadSchema = z.object({
  name: z.string().min(1, "Name ist erforderlich"),
  domain: z
    .string()
    .optional()
    .nullable()
    .refine((val) => !val || /^[a-z0-9.-]+\.[a-z]{2,}$/i.test(val), "Ungültige Domain"),
  status: z.enum(["new", "qualified", "lost"]).optional(),
  primary_contact: ContactSchema.optional(),
});

type Props = { onCreated?: () => void };

// Diese Komponente zeigt ein Formular zum Erstellen eines Leads inkl. optionalem Primärkontakt.
export default function LeadForm({ onCreated }: Props) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (lead: any) => createLead(lead),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      onCreated?.();
    },
  });

  const [form, setForm] = React.useState({
    name: "",
    domain: "",
    status: "new",
    first_name: "",
    last_name: "",
    emails: [{ value: "", is_primary: true }],
  });

  const [errors, setErrors] = React.useState<Record<string, any>>({});

  function onChange(key: string, value: any, index?: number) {
    if (key === "email") {
      const updatedEmails = [...form.emails];
      updatedEmails[index!] = { ...updatedEmails[index!], value };
      setForm({ ...form, emails: updatedEmails });
    } else if (key === "is_primary") {
      const updatedEmails = form.emails.map((e, i) => ({
        ...e,
        is_primary: i === index,
      }));
      setForm({ ...form, emails: updatedEmails });
    } else {
      setForm((prev) => ({ ...prev, [key]: value }));
    }
  }

  function addEmail() {
    setForm((prev) => ({ ...prev, emails: [...prev.emails, { value: "", is_primary: false }] }));
  }

  function removeEmail(index: number) {
    const updatedEmails = form.emails.filter((_, i) => i !== index);
    if (!updatedEmails.some((e) => e.is_primary) && updatedEmails.length > 0) updatedEmails[0].is_primary = true;
    setForm({ ...form, emails: updatedEmails });
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();

    const lead: any = {
      name: form.name,
      domain: form.domain || undefined,
      status: form.status,
    };

    if (form.first_name || form.last_name || form.emails.some((e) => e.value)) {
      lead.primary_contact = {
        first_name: form.first_name || undefined,
        last_name: form.last_name || undefined,
        emails: form.emails.filter((e) => e.value.trim() !== ""),
      };
    }

    const parsed = LeadSchema.safeParse(lead);
    if (!parsed.success) {
      setErrors(parsed.error.flatten().fieldErrors);
      return;
    }

    setErrors({});
    mutation.mutate(lead);
  }

  return (
    <form onSubmit={onSubmit} className="form-card">
      <h3>Neuen Lead anlegen</h3>

      <input
        value={form.name}
        onChange={(e) => onChange("name", e.target.value)}
        placeholder="Firma"
      />
      {errors.name && <div className="error">{errors.name.join(", ")}</div>}

      <input
        value={form.domain}
        onChange={(e) => onChange("domain", e.target.value)}
        placeholder="domain.example.com"
      />
      {errors.domain && <div className="error">{errors.domain.join(", ")}</div>}

      <select value={form.status} onChange={(e) => onChange("status", e.target.value)}>
        <option value="new">new</option>
        <option value="qualified">qualified</option>
        <option value="lost">lost</option>
      </select>

      <hr className="divider" />

      <h4>Primärer Kontakt (optional)</h4>

      <input
        value={form.first_name}
        onChange={(e) => onChange("first_name", e.target.value)}
        placeholder="Vorname"
      />
      {errors.primary_contact?.first_name && (
        <div className="error">{errors.primary_contact.first_name.join(", ")}</div>
      )}

      <input
        value={form.last_name}
        onChange={(e) => onChange("last_name", e.target.value)}
        placeholder="Nachname"
      />
      {errors.primary_contact?.last_name && (
        <div className="error">{errors.primary_contact.last_name.join(", ")}</div>
      )}

      {form.emails.map((email, index) => (
        <div key={index} className="email-row">
          <input
            className="email-input"
            value={email.value}
            onChange={(e) => onChange("email", e.target.value, index)}
            placeholder="Email"
          />
          <label className="primary-label">
            <input
              type="radio"
              checked={email.is_primary}
              onChange={() => onChange("is_primary", true, index)}
            />
            Primär
          </label>
          {form.emails.length > 1 && (
            <button type="button" className="remove-email" onClick={() => removeEmail(index)}>
              ×
            </button>
          )}
          {errors.primary_contact?.emails?.[index]?.value && (
            <div className="error">{errors.primary_contact.emails[index].value.join(", ")}</div>
          )}
        </div>
      ))}

      <button type="button" className="add-email-button" onClick={addEmail}>
        + Email hinzufügen
      </button>

      <button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Erstelle..." : "Erstellen"}
      </button>
    </form>
  );
}
