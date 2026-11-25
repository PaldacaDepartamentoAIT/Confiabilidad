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
  const setUser = useCallback((next: AuthenticatedUser | null) => {
    writeStoredUser(next);
    setState(next);
  }, []);

  useEffect(() => {
    if (sessionUser !== undefined) setUser(sessionUser);
  }, [sessionUser, setUser]);

  return <UserContext.Provider value={{ user, setUser }}>{children}</UserContext.Provider>;
}
