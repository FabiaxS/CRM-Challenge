import React, { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchLeads, setLeadStatus } from "../api/client";
import type { Lead } from "../api/client";
import LeadForm from "./LeadForm";

// Kleine Badge-Komponente für Status-Anzeige
function StatusBadge({ status }: { status: string }) {
  let className = "";
  if (status === "new") className = "status-badge status-new";
  else if (status === "qualified") className = "status-badge status-qualified";
  else className = "status-badge status-lost";
  
  return <span className={className}>{status}</span>;
}

// Hauptkomponente: LeadsList
export default function LeadsList({ q, status, page, setPage }: any) {
  const limit = 10;
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [sortField, setSortField] = useState<keyof Lead | "primary_contact" | "status">("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [editingStatusId, setEditingStatusId] = useState<number | null>(null);
  const selectRef = useRef<HTMLSelectElement | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["leads", { q, status, limit, offset: page * limit, sortField, sortOrder }],
    queryFn: () => fetchLeads(q, status, limit, page * limit, sortField, sortOrder),
  });

  const changeStatusMut = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => setLeadStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      setEditingStatusId(null);
    },
  });

  useEffect(() => {
    if (selectRef.current) {
      selectRef.current.focus();
      const event = new MouseEvent("mousedown", { bubbles: true });
      selectRef.current.dispatchEvent(event);
    }
  }, [editingStatusId]);

  function handleSort(field: keyof Lead | "primary_contact" | "status") {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  }

  function renderSortIcon(field: keyof Lead | "primary_contact" | "status") {
    if (sortField !== field) return "↕";
    return sortOrder === "asc" ? "↑" : "↓";
  }

  return (
    <div className="container-full">
      <div className="header-full">
        <h2>Leads</h2>
        <button className="add-lead-button" onClick={() => setShowForm(true)}>
          Lead hinzufügen
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowForm(false)}>×</button>
            <LeadForm onCreated={() => setShowForm(false)} />
          </div>
        </div>
      )}

      {isLoading ? (
        <div>Lädt...</div>
      ) : (
        <table className="table-full">
          <thead>
            <tr>
              <th onClick={() => handleSort("name")}>Name {renderSortIcon("name")}</th>
              <th onClick={() => handleSort("domain")}>Domain {renderSortIcon("domain")}</th>
              <th onClick={() => handleSort("primary_contact")}>
                Kontakt {renderSortIcon("primary_contact")}
              </th>
              <th onClick={() => handleSort("status")}>Status {renderSortIcon("status")}</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={4}>Keine Leads vorhanden</td>
              </tr>
            )}
            {data?.items.map((lead: Lead) => (
              <tr key={lead.id}>
                <td>{lead.name}</td>
                <td>{lead.domain}</td>
                <td>
                  {lead.primary_contact
                    ? `${lead.primary_contact.first_name} ${lead.primary_contact.last_name} • ${lead.primary_contact.emails?.[0]?.value}`
                    : "-"}
                </td>
                <td style={{ position: "relative" }}>
                  {editingStatusId === lead.id ? (
                    <select
                      ref={selectRef}
                      value={lead.status}
                      onChange={(e) => {
                        changeStatusMut.mutate({ id: lead.id, status: e.target.value });
                      }}
                      onBlur={() => setEditingStatusId(null)}
                      className="inline-status-select absolute-dropdown"
                    >
                      <option value="new">new</option>
                      <option value="qualified">qualified</option>
                      <option value="lost">lost</option>
                    </select>
                  ) : (
                    <span onClick={() => setEditingStatusId(lead.id)}>
                      <StatusBadge status={lead.status} />
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="pagination-full">
        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}>
          Prev
        </button>
        <span>
          {page * limit + 1} - {Math.min((page + 1) * limit, data?.total)} von {data?.total}
        </span>
        <button onClick={() => setPage(page + 1)} disabled={(page + 1) * limit >= data?.total}>
          Next
        </button>
      </div>
    </div>
  );
}
