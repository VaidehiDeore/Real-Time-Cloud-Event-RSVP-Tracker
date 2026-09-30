import {
  CalendarDays,
  LayoutDashboard,
  Users,
  BarChart3,
  Bell,
  LogOut
} from "lucide-react";

export default function Sidebar({ user, onLogout, page, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="logo">ER</div>

        <div>
          <b>Evently</b>
          <span>Cloud RSVP</span>
        </div>
      </div>

      <nav>
        <a
          href="#"
          className={page === "dashboard" ? "active" : ""}
          onClick={(e) => {
            e.preventDefault();
            onNavigate("dashboard");
          }}
        >
          <LayoutDashboard size={18} />
          Dashboard
        </a>

        <a
          href="#"
          className={page === "events" ? "active" : ""}
          onClick={(e) => {
            e.preventDefault();
            onNavigate("events");
          }}
        >
          <CalendarDays size={18} />
          Events
        </a>

        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            onNavigate("invitees");
          }}
        >
          <Users size={18} />
          Invitees
        </a>

        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            onNavigate("analytics");
          }}
        >
          <BarChart3 size={18} />
          Analytics
        </a>

        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            onNavigate("notifications");
          }}
        >
          <Bell size={18} />
          Notifications
        </a>
      </nav>

      <div className="profile">
        <div className="avatar">
          {user?.name?.[0]?.toUpperCase()}
        </div>

        <div className="profileText">
          <b>{user?.name}</b>
          <span>{user?.role}</span>
        </div>

        <button onClick={onLogout} title="Sign out">
          <LogOut size={17} />
        </button>
      </div>
    </aside>
  );
}
