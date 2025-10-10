import React from "react";
import LeadsList from "../components/LeadsList";

function useDebouncedState(initial = "", ms = 350) {
  const [raw, setRaw] = React.useState(initial);
  const debounced = useDebounce(raw, ms);
  return { raw, setRaw, debounced };
}

export function useDebounce<T>(value: T, delay = 300) {
  const [debouncedValue, setDebouncedValue] = React.useState(value);
  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}

export default function Home() {
  const qState = useDebouncedState("", 400);
  const [statusFilter, setStatusFilter] = React.useState("");
  const [page, setPage] = React.useState(0);

  return (
    <div className="container-full">
      <h1>Mini Lead CRM</h1>

      <div className="filters-full">
        <input
          placeholder="Search by name or domain..."
          value={qState.raw}
          onChange={(e) => { qState.setRaw(e.target.value); setPage(0); }}
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
        >
          <option value="">All</option>
          <option value="new">new</option>
          <option value="qualified">qualified</option>
          <option value="lost">lost</option>
        </select>
      </div>

      <LeadsList
        q={qState.debounced}
        status={statusFilter || undefined}
        page={page}
        setPage={setPage}
      />
    </div>
  );
}
