import type { TFunction } from "i18next";
import type { MouseEvent } from "react";

import type { AuthenticatedUser } from "../api/auth";
import { IconHouse, IconLogOut, IconUser } from "../icons";
import type { SidebarItem, SidebarUser } from "../layouts/Sidebar";
import { navigate } from "../routing/router";

function go(href: string) {
  return (event: MouseEvent<HTMLAnchorElement>) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) {
      return;
    }
    event.preventDefault();
    navigate(href);
  };
}

export function privateNavItems(t: TFunction): SidebarItem[] {
  return [
    { id: "home", label: t("auth.homeTitle"), href: "/", icon: <IconHouse />, onSelect: go("/") },
    {
      id: "profile",
      label: t("auth.profileNav"),
      href: "/profile",
      icon: <IconUser />,
      onSelect: go("/profile"),
    },
  ];
}

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
