import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Spiegelt das Datenmodell aus dem Backend (LeadRead Schema) wider.
export type Lead = {
  id: number;
  name: string;
  domain?: string;
  status: "new" | "qualified" | "lost";
  created_at: string;
  primary_contact?: {
    id: number;
    first_name?: string;
    last_name?: string;
    emails: { id: number; value: string; is_primary: boolean }[];
  } | null;
};

// GET /leads
export async function fetchLeads(
  q?: string,
  status?: string,
  limit = 20,
  offset = 0,
  sortField?: keyof Lead | "primary_contact" | "status",
  sortOrder: "asc" | "desc" = "asc"
) {
  const params: any = { limit, offset };
  if (q) params.q = q;
  if (status) params.status = status;

  const res = await API.get("/leads", { params });
  let data = res.data;

  // Sortierung im Frontend (nach Name, Domain, Status oder Primärkontakt)
  if (Array.isArray(data.items) && sortField) {
    data.items.sort((a: Lead, b: Lead) => {
      let aValue: string = "";
      let bValue: string = "";

      switch (sortField) {
        case "name":
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case "domain":
          aValue = (a.domain || "").toLowerCase();
          bValue = (b.domain || "").toLowerCase();
          break;
        case "status":
          aValue = a.status;
          bValue = b.status;
          break;
        case "primary_contact":
          aValue = ((a.primary_contact?.first_name || "") + (a.primary_contact?.last_name || "")).toLowerCase();
          bValue = ((b.primary_contact?.first_name || "") + (b.primary_contact?.last_name || "")).toLowerCase();
          break;
      }

      if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
      if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });
  }

  return data;
}

// POST /leads
export async function createLead(lead: any) {
  const res = await API.post("/leads", lead);
  return res.data;
}

// POST /leads/{id}/status?new_status=<status>
export async function setLeadStatus(id: number, status: string) {
  const res = await API.post(`/leads/${id}/status`, null, {
    params: { new_status: status },
  });
  return res.data;
}
