import { Avatar, Button, Drawer } from "@heroui/react";
import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const NAV = [
  { to: "/", label: "Dashboard", icon: "▦" },
  { to: "/medications", label: "Medications", icon: "💊" },
  { to: "/scan", label: "Scan", icon: "📷" },
  { to: "/scans", label: "Scan history", icon: "🗒️" },
  { to: "/profile", label: "Profile", icon: "👤" },
];

function SidebarLinks() {
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === "/"}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              isActive ? "bg-blue-50 text-blue-700" : "text-gray-600 hover:bg-gray-100"
            }`
          }
        >
          <span>{item.icon}</span>
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

export default function Layout({ children }: { children: ReactNode }) {
  const { email, logout } = useAuth();
  const navigate = useNavigate();
  const initials = (email ?? "?").slice(0, 2).toUpperCase();

  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-900">
      {/* Desktop sidebar */}
      <aside className="hidden w-60 flex-col gap-1 border-r border-gray-200 bg-white p-4 md:flex">
        <div className="mb-6 flex items-center gap-2 px-2 text-xl font-bold">🛡️ DoseGuard</div>
        <SidebarLinks />
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 md:px-6">
          <div className="flex items-center gap-2">
            {/* Mobile hamburger -> Drawer */}
            <div className="md:hidden">
              <Drawer>
                <Button isIconOnly size="sm" variant="tertiary" aria-label="Open menu">
                  ☰
                </Button>
                <Drawer.Backdrop>
                  <Drawer.Content placement="left">
                    <Drawer.Dialog>
                      <Drawer.CloseTrigger />
                      <Drawer.Header>
                        <Drawer.Heading>🛡️ DoseGuard</Drawer.Heading>
                      </Drawer.Header>
                      <Drawer.Body>
                        <nav className="flex flex-col gap-1">
                          {NAV.map((item) => (
                            <Button
                              key={item.to}
                              slot="close"
                              variant="ghost"
                              className="justify-start"
                              onPress={() => navigate(item.to)}
                            >
                              <span className="mr-2">{item.icon}</span>
                              {item.label}
                            </Button>
                          ))}
                        </nav>
                      </Drawer.Body>
                    </Drawer.Dialog>
                  </Drawer.Content>
                </Drawer.Backdrop>
              </Drawer>
            </div>
            <span className="font-semibold md:hidden">DoseGuard</span>
            <span className="hidden text-sm text-gray-500 md:inline">Medication safety</span>
          </div>

          <div className="flex items-center gap-3">
            <Avatar size="sm">
              <Avatar.Fallback>{initials}</Avatar.Fallback>
            </Avatar>
            <span className="hidden text-sm sm:inline">{email}</span>
            <Button size="sm" variant="tertiary" onPress={() => logout()}>
              Log out
            </Button>
          </div>
        </header>
         <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
