import { Avatar, Button, Drawer } from "@heroui/react";
import { AnimatePresence, motion } from "framer-motion";
import {
  CalendarDays,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Pill,
  ScanLine,
  Shield,
  User,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const NAV: { to: string; label: string; icon: LucideIcon }[] = [
  { to: "/today", label: "Today", icon: CalendarDays },
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/medications", label: "Medications", icon: Pill },
  { to: "/scan", label: "Scan", icon: ScanLine },
  { to: "/scans", label: "Scan history", icon: History },
  { to: "/profile", label: "Profile", icon: User },
];

function SidebarLinks() {
  return (
    <nav className="flex flex-col gap-1">
      {NAV.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink key={item.to} to={item.to} end={item.to === "/"}>
            {({ isActive }) => (
              <div
                className={`relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "text-brand" : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="navPill"
                    className="absolute inset-0 rounded-lg bg-brand-soft"
                    transition={{ type: "spring", stiffness: 400, damping: 32 }}
                  />
                )}
                <Icon className="relative size-4" />
                <span className="relative">{item.label}</span>
              </div>
            )}
          </NavLink>
        );
      })}
    </nav>
  );
}

export default function Layout({ children }: { children: ReactNode }) {
  const { email, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const initials = (email ?? "?").slice(0, 2).toUpperCase();

  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-900">
      {/* Desktop sidebar */}
      <aside className="hidden w-60 flex-col gap-1 border-r border-gray-200 bg-white p-4 md:flex">
        <div className="mb-6 flex items-center gap-2 px-2 text-xl font-bold">
          <Shield className="size-5 text-brand" /> DoseGuard
        </div>
        <SidebarLinks />
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 md:px-6">
          <div className="flex items-center gap-2">
            {/* Mobile hamburger -> Drawer */}
            <div className="md:hidden">
              <Drawer>
                <Button isIconOnly size="sm" variant="tertiary" aria-label="Open menu">
                  <Menu className="size-4" />
                </Button>
                <Drawer.Backdrop>
                  <Drawer.Content placement="left">
                    <Drawer.Dialog>
                      <Drawer.CloseTrigger />
                      <Drawer.Header>
                        <Drawer.Heading className="flex items-center gap-2">
                          <Shield className="size-5 text-brand" /> DoseGuard
                        </Drawer.Heading>
                      </Drawer.Header>
                      <Drawer.Body>
                        <nav className="flex flex-col gap-1">
                          {NAV.map((item) => {
                            const Icon = item.icon;
                            return (
                              <Button
                                key={item.to}
                                slot="close"
                                variant="ghost"
                                className="justify-start"
                                onPress={() => navigate(item.to)}
                              >
                                <Icon className="mr-2 size-4" />
                                {item.label}
                              </Button>
                            );
                          })}
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
              <LogOut className="mr-1 size-4" /> Log out
            </Button>
          </div>
        </header>

        {/* Page transition */}
        <main className="flex-1 p-4 md:p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );

}
