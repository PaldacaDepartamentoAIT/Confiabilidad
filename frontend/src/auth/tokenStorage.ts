export const SESSION_TOKEN_KEY = "confiabilidad.sessionToken";

export type StorageBackend = Pick<Storage, "getItem" | "setItem" | "removeItem">;

export type TokenStorage = {
  get: () => string | null;
  set: (token: string) => void;
  clear: () => void;
};

function defaultBackend(): StorageBackend | null {
  try {
    return typeof window !== "undefined" ? window.localStorage : null;
  } catch {
    return null;
  }
}

export function createTokenStorage(backend?: StorageBackend | null): TokenStorage {
  let memory: string | null = null;
  const resolve = () => (backend === undefined ? defaultBackend() : backend);
  return {
    get: () => {
      try {
        const store = resolve();
        if (store) return store.getItem(SESSION_TOKEN_KEY);
      } catch {
        // Respaldo en memoria si localStorage no está disponible.
      }
      return memory;
    },
    set: (token: string) => {
      memory = token;
      try {
        resolve()?.setItem(SESSION_TOKEN_KEY, token);
      } catch {
        // Conserva el valor en memoria si el almacenamiento falla.
      }
    },
    clear: () => {
      memory = null;
      try {
        resolve()?.removeItem(SESSION_TOKEN_KEY);
      } catch {
        // Ya quedó limpio en memoria.
      }
    },
  };
}

export const tokenStorage: TokenStorage = createTokenStorage();
