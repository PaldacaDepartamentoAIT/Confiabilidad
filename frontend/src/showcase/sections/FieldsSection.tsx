import { useId } from "react";

import { Checkbox } from "../../components/fields/Checkbox";
import { CodeField } from "../../components/fields/CodeField";
import { PasswordField } from "../../components/fields/PasswordField";
import { TextField } from "../../components/fields/TextField";
import "./sections.css";

// Contenido de ejemplo del catálogo: inventado y en español (S-03), por eso lleva su propio `lang`.
export function FieldsSection() {
  const titleId = useId();
  return (
    <div role="region" aria-labelledby={titleId} lang="es" className="catalog-section">
      <h2 id={titleId}>Campos</h2>
      <div className="catalog-grid">
        <TextField label="Razón social" required defaultValue="Hidroeléctrica del Norte S. A." />
        <TextField label="Nombre comercial" hint="Como lo conocen los clientes." />
        <TextField
          label="NIF/CIF"
          className="mono"
          defaultValue="B1234567"
          error="El NIF/CIF debe tener 9 caracteres."
        />
        <PasswordField label="Clave de acceso" kind="current" />
        <CodeField label="Código" defaultValue="123456" />
      </div>
      <div className="catalog-stack">
        <Checkbox
          label="Empresa activa"
          hint="Las empresas inactivas no aparecen al registrar activos."
          defaultChecked
        />
        <Checkbox label="Recibir avisos por correo" />
        <Checkbox label="Acepto los términos" required error="Debes aceptar los términos." />
      </div>
    </div>
  );
}
