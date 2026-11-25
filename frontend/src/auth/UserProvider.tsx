import { useCallback, useEffect, useState, type ReactNode } from "react";

import type { AuthenticatedUser } from "../api/auth";
import { UserContext, readStoredUser, writeStoredUser } from "./privateNav";

export function UserProvider({
  sessionUser,
  children,
}: {
  sessionUser?: AuthenticatedUser | null;
  children: ReactNode;
}) {
  const [user, setState] = useState<AuthenticatedUser | null>(
    () => sessionUser ?? readStoredUser(),
  );
  const [collapsed, setCollapsed] = useState(false);
  const setUser = useCallback((next: AuthenticatedUser | null) => {
    writeStoredUser(next);
    setState(next);
  }, []);

  useEffect(() => {
    if (sessionUser !== undefined) setUser(sessionUser);
    if (sessionUser === null) setCollapsed(false);
  }, [sessionUser, setUser]);

  return (
    <UserContext.Provider value={{ user, setUser, collapsed, setCollapsed }}>
      {children}
    </UserContext.Provider>
  );
}
