import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LeadsList from "../components/LeadsList";
import { vi } from "vitest";

vi.mock("../api/client", () => ({
  fetchLeads: vi.fn(() => Promise.resolve({ items: [], total: 0 })),
  setLeadStatus: vi.fn(),
}));

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
        {ui}
    </QueryClientProvider>
  );
}

describe("LeadsList", () => {
  it("Öffnet das Lead-Formular, wenn man auf 'Lead hinzufügen' klickt", async () => {
    renderWithClient(<LeadsList q={""} status={""} page={0} setPage={() => {}} />);

    // Modal sollte anfangs nicht sichtbar sein
    expect(screen.queryByText(/Neuen Lead anlegen/i)).toBeNull();

    // Button "Lead hinzufügen" klicken
    fireEvent.click(screen.getByText(/Lead hinzufügen/i));

    // Modal sollte jetzt sichtbar sein
    await waitFor(() =>
      expect(screen.getByText(/Neuen Lead anlegen/i)).toBeInTheDocument()
    );
  });
});
