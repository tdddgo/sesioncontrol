# Cómo publicar en XYZ Sevilla

Cada persona escribe sus noticias en **Google Docs** y las sube a **su carpeta** de Drive.
La web se regenera sola cada 15 minutos. No hay que avisar a nadie ni tocar código.

## Reglas

1. **Una carpeta por persona.** Dentro de la carpeta compartida `XYZ Sevilla - Redacción` hay una subcarpeta con tu nombre. Solo subes ahí. El nombre de la carpeta es tu firma si no pones `Autor:`.
2. **Un Google Doc por noticia.** Duplica el Doc `PLANTILLA` y rellénalo. No cambies los nombres de los campos.
3. **La cabecera va arriba, una línea por campo, seguida de una línea con `---`.** Debajo de `---` va el texto de la noticia (párrafos separados por una línea en blanco).
4. **`Publicar: si` para que salga.** Con `no` (o sin el campo) queda como borrador y no se ve en la web.
5. **La sección debe ser una de la lista:** Mesa del Congreso, Presidente de Gobierno, Ministros, Diputados oficialistas, Diputados de oposición, Otro grupo de oposición. Elige el grupo al que pertenece tu rol.
6. **Imágenes y audios (podcast).** Súbelos a tu carpeta, junto al Doc, o a la carpeta compartida `Insumos` (subcarpetas `Imagenes` y `Audios`) si los usará más de una persona. En el Doc pones el nombre exacto del archivo en `Imagen:` o `Audio:`; se busca primero en tu carpeta y después en `Insumos`.
   - Imagen: JPG, PNG o WEBP, máximo 2 MB, horizontal. Solo fotos propias o libres de derechos, con crédito en `Credito:`.
   - Audio: MP3, M4A, WAV u OGG, máximo 25 MB (un episodio corto, de 10 a 20 minutos en MP3 128 kbps, cabe de sobra). Saldrá un reproductor en la noticia y un bloque «Podcast» en la portada. Pon la transcripción o un resumen como texto de la noticia.
   - Dos archivos con el mismo nombre en distintas carpetas son una fuente de errores: usa nombres únicos, por ejemplo `ministros-puente-01.jpg`.
7. **Para corregir, edita el mismo Doc.** No hagas copias; se actualiza en el siguiente ciclo. Para retirar una noticia pon `Publicar: no`.
8. **No muevas ni renombres las carpetas de otras personas** ni la carpeta raíz.
9. **Si algo está mal escrito, la noticia no rompe la web:** se omite y aparece en el informe de errores (pestaña *Actions* del repositorio, paso "Informe").

## Plantilla del Doc

```
Titulo: Titular de la noticia
Seccion: Ministros
Autor: Nombre Apellido
Entradilla: Una o dos frases que resumen la noticia.
Imagen: foto.jpg
Credito: Foto: Nombre
Audio: episodio.mp3
Destacada: no
Publicar: si
---
Primer párrafo del texto.

Segundo párrafo del texto.
```

Campos obligatorios: `Titulo`, `Seccion`, `Publicar`. El resto es opcional (si no usas `Audio`, borra esa línea o déjala vacía).
`Destacada: si` la coloca en la apertura de la portada (si hay varias, gana la más reciente).

## Qué hace el sistema (para el equipo técnico)

- `build.py` lee la carpeta de Drive con una cuenta de servicio de solo lectura, genera la web en `public/` y la publica en GitHub Pages.
- Se ejecuta cada 15 min y también a mano desde *Actions → Actualizar web → Run workflow*.
- Si el build falla, se mantiene la última versión publicada.
- Configuración única: ver los pasos al final de `README-despliegue.md`.
