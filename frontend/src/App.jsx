import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import Events from "./pages/Events";

function PlaceholderPage({ title, description }) {
  return (
    <section className="page">
      <div className="pageHeader">
        <div>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </div>

      <div className="emptyState">
        <h3>{title}</h3>
        <p>This section is connected to the navigation. We will build the full functionality next.</p>
      </div>
    </section>
  );
}

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("user"));
    } catch {
      return null;
    }
  });

  const [page, setPage] = useState("dashboard");

  const logout = () => {
    localStorage.clear();
    setUser(null);
    setPage("dashboard");
  };

  if (!user) {
    return <Auth onAuth={setUser} />;
  }

  return (
    <div className="app">
      <Sidebar
        user={user}
        onLogout={logout}
        page={page}
        onNavigate={setPage}
      />

      <main className="main">
        {page === "dashboard" && <Dashboard user={user} />}

        {page === "events" && (
          <Events onCreateEvent={() => setPage("dashboard")} />
        )}

        {page === "invitees" && (
          <PlaceholderPage
            title="Invitees"
            description="Manage event invitees, RSVP responses and attendee status."
          />
        )}

        {page === "analytics" && (
          <PlaceholderPage
            title="Analytics"
            description="View RSVP statistics, capacity utilization and event performance."
          />
        )}

        {page === "notifications" && (
          <PlaceholderPage
            title="Notifications"
            description="View RSVP confirmations, announcements and event updates."
          />
        )}
      </main>
    </div>
  );
}
