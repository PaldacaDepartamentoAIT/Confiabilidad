import type { TFunction } from "i18next";
import { createContext, useContext, type MouseEvent } from "react";

import type { AuthenticatedUser } from "../api/auth";
import { IconHouse, IconLogOut, IconUser } from "../icons";
import type { SidebarItem, SidebarUser } from "../layouts/Sidebar";
import { navigate } from "../routing/router";

export const USER_STORAGE_KEY = "confiabilidad.user";

export function readStoredUser(): AuthenticatedUser | null {
  try {
    const raw = window.sessionStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as Partial<AuthenticatedUser>;
    return typeof data.email === "string"
      ? { email: data.email, name: typeof data.name === "string" ? data.name : "" }
      : null;
  } catch {
    return null;
  }
}

export function writeStoredUser(user: AuthenticatedUser | null) {
  try {
    if (user) {
      window.sessionStorage.setItem(
        USER_STORAGE_KEY,
        JSON.stringify({ email: user.email, name: user.name }),
      );
    } else {
      window.sessionStorage.removeItem(USER_STORAGE_KEY);
    }
  } catch {
    // El almacenamiento de sesión puede estar deshabilitado.
  }
}

export const UserContext = createContext<{
  user: AuthenticatedUser | null;
  setUser: (user: AuthenticatedUser | null) => void;
}>({
  user: null,
  setUser: writeStoredUser,
});

export function usePrivateUser() {
  return useContext(UserContext);
}

const go = (href: string) => (e: MouseEvent<HTMLAnchorElement>) => {
  if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
  e.preventDefault();
  navigate(href);
};

export const privateNavItems = (t: TFunction): SidebarItem[] => [
  { id: "home", label: t("auth.homeTitle"), href: "/", icon: <IconHouse />, onSelect: go("/") },
  {
    id: "profile",
    label: t("auth.profileNav"),
    href: "/profile",
    icon: <IconUser />,
    onSelect: go("/profile"),
  },
];

export function privateSidebarUser(
  user: AuthenticatedUser | null | undefined,
  t: TFunction,
  onLogout: () => void,
): SidebarUser | undefined {
  if (!user) return undefined;
  const parts = (user.name || user.email || "U").trim().split(/\s+/);
  const initials = (
    parts.length >= 2 ? `${parts[0][0]}${parts[1][0]}` : parts[0].slice(0, 2)
  ).toUpperCase();
  return {
    name: user.name || user.email,
    initials,
    menu: [{ id: "logout", label: t("auth.logout"), icon: <IconLogOut />, onSelect: onLogout }],
  };
}
