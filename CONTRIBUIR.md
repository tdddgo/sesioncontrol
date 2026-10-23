# Cómo publicar en red.es

Cada persona escribe sus noticias en **Google Docs** y las sube a **su carpeta** de Drive.
La web se regenera sola cada 15 minutos. No hay que avisar a nadie ni tocar código.

## Reglas

1. **Una carpeta por grupo.** Dentro de la carpeta compartida [`red.es - Redacción`](https://drive.google.com/drive/folders/1j8TWIuNdkeHwfWBsMqghXD1lWVmQBPKg) hay una subcarpeta por grupo (Mesa del Congreso, Presidente de Gobierno, Ministros, Diputados oficialistas, Diputados de oposición, Otro grupo de oposición, Sociedad). Subes tu Doc a la carpeta de tu grupo: esa carpeta decide en qué sección sale la noticia. Tu firma es el campo `Autor:`.
2. **Un Google Doc por noticia.** Duplica el Doc [`PLANTILLA`](https://docs.google.com/document/d/16x2O3Cijz7Lvfqz_PiFf6GHttNqSJTU0rv7iR0wEFvk/edit) y rellénalo. No cambies los nombres de los campos.
3. **La cabecera va arriba, una línea por campo, seguida de una línea con `---`.** Debajo de `---` va el texto de la noticia (párrafos separados por una línea en blanco).
4. **`Publicar: si` para que salga.** Con `no` (o sin el campo) queda como borrador y no se ve en la web.
5. **La sección debe ser una de la lista:** Mesa del Congreso, Presidente de Gobierno, Ministros, Diputados oficialistas, Diputados de oposición, Otro grupo de oposición, Sociedad (reportajes sobre los temas de los que habla la ciudadanía). Elige el grupo al que pertenece tu rol.
6. **Imágenes y audios (podcast).** Súbelos a la carpeta de tu grupo, junto al Doc, o a la carpeta compartida [`Insumos`](https://drive.google.com/drive/folders/1JF1n57z4yJAPKrpNDeuXCCVyqmd8yInG) (subcarpetas `Imagenes` y `Audios`) si los usará más de una persona. En el Doc pones el nombre exacto del archivo en `Imagen:` o `Audio:`; se busca primero en la carpeta de tu grupo y después en `Insumos`.
   - Imagen: JPG, PNG o WEBP, máximo 2 MB, horizontal. Solo fotos propias o libres de derechos, con crédito en `Credito:`.
   - Audio: MP3, M4A, WAV u OGG, máximo 25 MB (un episodio corto, de 10 a 20 minutos en MP3 128 kbps, cabe de sobra). Saldrá un reproductor en la noticia y un bloque «Podcast» en la portada. Pon la transcripción o un resumen como texto de la noticia.
   - Dos archivos con el mismo nombre en distintas carpetas son una fuente de errores: usa nombres únicos, por ejemplo `ministros-puente-01.jpg`.
7. **Para corregir, edita el mismo Doc.** No hagas copias; se actualiza en el siguiente ciclo. Para retirar una noticia pon `Publicar: no`.
8. **No muevas ni renombres las carpetas de los grupos** ni la carpeta raíz.
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

## Enlaces

- Web: https://tdddgo.github.io/sesioncontrol/
- Carpeta raíz: https://drive.google.com/drive/folders/1j8TWIuNdkeHwfWBsMqghXD1lWVmQBPKg
- Insumos (imágenes y audios): https://drive.google.com/drive/folders/1JF1n57z4yJAPKrpNDeuXCCVyqmd8yInG
- Plantilla del Doc: https://docs.google.com/document/d/16x2O3Cijz7Lvfqz_PiFf6GHttNqSJTU0rv7iR0wEFvk/edit
- Guía en PDF: [como-aportar.pdf](como-aportar.pdf)

## Qué hace el sistema (para el equipo técnico)

- `build.py` lee la carpeta de Drive con una cuenta de servicio de solo lectura, genera la web en `public/` y la publica en GitHub Pages.
- Se ejecuta cada 15 min y también a mano desde *Actions → Actualizar web → Run workflow*.
- Si el build falla, se mantiene la última versión publicada.
- Configuración única: ver los pasos al final de `README-despliegue.md`.
