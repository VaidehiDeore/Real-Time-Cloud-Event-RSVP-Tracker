import { useEffect, useState } from "react";
import { CalendarDays, Plus, Search, Users, MapPin, Clock3 } from "lucide-react";
import { api } from "../services/api";

export default function Events({ onCreateEvent }) {
  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadEvents() {
    try {
      setLoading(true);
      setError("");
      const data = await api.events();
      setEvents(Array.isArray(data) ? data : data.events || []);
    } catch (err) {
      setError(err.message || "Unable to load events");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEvents();
  }, []);

  const filtered = events.filter((event) => {
    const text = [
      event.event_name,
      event.name,
      event.title,
      event.event_type,
      event.venue,
      event.status,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return text.includes(search.toLowerCase());
  });

  function formatDate(value) {
    if (!value) return "Date not set";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString(undefined, {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  return (
    <section className="page">
      <div className="pageHeader">
        <div>
          <div className="eyebrow">
            <CalendarDays size={15} />
            EVENT MANAGEMENT
          </div>
          <h1>Events</h1>
          <p>Manage your events, capacity and RSVP activity.</p>
        </div>

        <button className="primaryButton" onClick={onCreateEvent}>
          <Plus size={18} />
          Create Event
        </button>
      </div>

      <div className="toolbar">
        <div className="searchBox">
          <Search size={17} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search events..."
          />
        </div>
      </div>

      {loading && (
        <div className="emptyState">
          <CalendarDays size={28} />
          <h3>Loading events...</h3>
          <p>Fetching your events from the backend.</p>
        </div>
      )}

      {!loading && error && (
        <div className="errorState">
          <h3>Unable to load events</h3>
          <p>{error}</p>
          <button className="secondaryButton" onClick={loadEvents}>
            Try Again
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="emptyState">
          <CalendarDays size={32} />
          <h3>No events found</h3>
          <p>Create an event or change your search.</p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="eventGrid">
          {filtered.map((event) => {
            const capacity =
              event.maximum_capacity ??
              event.capacity ??
              0;

            const going =
              event.going_count ??
              event.going ??
              0;

            const percentage =
              capacity > 0
                ? Math.min(100, Math.round((going / capacity) * 100))
                : 0;

            return (
              <article className="eventCard" key={event.id || event.event_id}>
                <div className="eventCardTop">
                  <span className="eventType">
                    {event.event_type || "EVENT"}
                  </span>

                  <span className={`statusBadge ${(event.status || "PUBLISHED").toLowerCase()}`}>
                    {event.status || "PUBLISHED"}
                  </span>
                </div>

                <h2>
                  {event.event_name ||
                    event.name ||
                    event.title ||
                    "Untitled Event"}
                </h2>

                <p className="eventDescription">
                  {event.description || "No description available."}
                </p>

                <div className="eventMeta">
                  <span>
                    <CalendarDays size={16} />
                    {formatDate(event.event_date || event.date || event.start_at)}
                  </span>

                  <span>
                    <Clock3 size={16} />
                    {event.start_time || "Time not set"}
                  </span>

                  <span>
                    <MapPin size={16} />
                    {event.venue || "Online / Venue not set"}
                  </span>
                </div>

                <div className="capacityHeader">
                  <span>
                    <Users size={16} />
                    Capacity
                  </span>
                  <strong>
                    {going}/{capacity}
                  </strong>
                </div>

                <div className="capacityBar">
                  <div style={{ width: `${percentage}%` }} />
                </div>

                <div className="eventFooter">
                  <span>{percentage}% occupied</span>
                  <button className="textButton">
                    View Details
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
