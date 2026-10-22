# Despliegue (una sola vez)

1. **Drive:** crea la carpeta `red.es - Redacción` con una subcarpeta por persona y el Doc `PLANTILLA` (ver CONTRIBUIR.md). Copia el ID de la carpeta (la parte final de su URL).
2. **Cuenta de servicio:** en Google Cloud crea un proyecto, activa *Google Drive API*, crea una cuenta de servicio y descarga su clave JSON. Comparte la carpeta raíz de Drive con el email de esa cuenta como **Lector**.
3. **GitHub:** sube este proyecto a un repositorio. En *Settings → Secrets and variables → Actions* crea:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` = contenido completo del JSON
   - `DRIVE_FOLDER_ID` = ID de la carpeta raíz
4. **Pages:** *Settings → Pages → Source: GitHub Actions*.
5. Ejecuta *Actions → Actualizar web → Run workflow*. Desde ahí se actualiza solo cada 15 min.

Prueba local sin Drive: `python3 build.py --local contenido-ejemplo` y abre `public/index.html` con `python3 -m http.server -d public`.

Nota: GitHub puede retrasar las ejecuciones programadas unos minutos y las desactiva tras 60 días sin actividad en el repo.
