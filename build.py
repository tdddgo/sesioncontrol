#!/usr/bin/env python3
"""Genera la web de XYZ Sevilla en public/ a partir de Google Docs (Drive) o de una carpeta local.

Uso:
  python build.py --local contenido-ejemplo     # prueba sin Drive
  python build.py --drive                       # usa GOOGLE_SERVICE_ACCOUNT_JSON y DRIVE_FOLDER_ID
"""
import argparse, html, io, json, os, re, shutil, sys, unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "public"
SECCIONES = ["Mesa del Congreso", "Presidente de Gobierno", "Ministros", "Diputados oficialistas",
             "Diputados de oposición", "Otro grupo de oposición"]
CAMPOS = {"titulo", "seccion", "autor", "entradilla", "imagen", "credito", "audio", "destacada", "publicar", "fecha"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMG = 2 * 1024 * 1024
AUDIO_EXT = {".mp3", ".m4a", ".wav", ".ogg"}
MAX_AUDIO = 25 * 1024 * 1024
CARPETA_COMPARTIDA = "insumos"   # carpeta de imágenes y audios disponibles para todos

esc = html.escape


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "sin-titulo"


def norm_key(s):
    return slugify(s).replace("-", "")


# ---------- Lectura de fuentes ----------
def parse_doc(text, persona, nombre_origen, modificado):
    """Devuelve (articulo, None) o (None, error)."""
    text = text.replace("﻿", "").replace("\r\n", "\n").replace("\r", "\n")
    cab, sep, cuerpo = text.partition("\n---")
    if not sep:
        return None, "falta la línea '---' que separa la cabecera del texto"
    meta = {}
    for line in cab.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            k = norm_key(k)
            if k in CAMPOS:
                meta[k] = v.strip()
    cuerpo = cuerpo.lstrip("-").strip()
    for obl in ("titulo", "seccion", "publicar"):
        if not meta.get(obl):
            return None, f"falta el campo obligatorio '{obl.capitalize()}'"
    if meta["publicar"].lower() not in ("si", "sí"):
        return None, "BORRADOR"
    secc = next((s for s in SECCIONES if norm_key(s) == norm_key(meta["seccion"])), None)
    if not secc:
        return None, f"sección '{meta['seccion']}' no válida"
    fecha = modificado
    if meta.get("fecha"):
        try:
            fecha = datetime.fromisoformat(meta["fecha"]).replace(tzinfo=timezone.utc)
        except ValueError:
            return None, "Fecha debe tener formato AAAA-MM-DD"
    return {
        "titulo": meta["titulo"], "seccion": secc, "autor": meta.get("autor") or persona,
        "entradilla": meta.get("entradilla", ""), "imagen_nombre": meta.get("imagen", ""), "audio_nombre": meta.get("audio", ""),
        "credito": meta.get("credito", ""), "destacada": meta.get("destacada", "").lower() in ("si", "sí"),
        "cuerpo": cuerpo, "fecha": fecha, "persona": persona, "origen": nombre_origen,
    }, None


def leer_local(carpeta):
    """Devuelve (docs, medios). medios[(persona, nombre)] = (tamaño, función que devuelve los bytes).
    Los archivos de la carpeta Insumos se guardan con persona "*" (sirven para todos)."""
    base = Path(carpeta)
    docs, medios = [], {}
    for d in sorted(x for x in base.iterdir() if x.is_dir()):
        compartida = norm_key(d.name) == CARPETA_COMPARTIDA
        for p in sorted(d.rglob("*") if compartida else d.glob("*")):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext == ".txt" and not compartida:
                mod = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)
                docs.append((d.name, p.name, p.read_text(encoding="utf-8"), mod))
            elif ext in IMG_EXT | AUDIO_EXT:
                medios[("*" if compartida else d.name, p.name)] = (p.stat().st_size, p.read_bytes)
    return docs, medios


def leer_drive(folder_id):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2 import service_account

    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)

    def listar(pid):
        items, token = [], None
        while True:
            r = svc.files().list(q=f"'{pid}' in parents and trashed=false", pageToken=token,
                                 fields="nextPageToken, files(id,name,mimeType,modifiedTime,size)",
                                 pageSize=200).execute()
            items += r["files"]
            token = r.get("nextPageToken")
            if not token:
                return items

    def descargador(fid):
        def bajar():
            buf = io.BytesIO()
            dl = MediaIoBaseDownload(buf, svc.files().get_media(fileId=fid), chunksize=8 * 1024 * 1024)
            done = False
            while not done:
                _, done = dl.next_chunk()
            return buf.getvalue()
        return bajar

    def es_medio(f):
        ext = Path(f["name"]).suffix.lower()
        return f["mimeType"].startswith(("image/", "audio/")) or ext in IMG_EXT | AUDIO_EXT

    def recoger_compartida(fid, nivel=0):
        for f in listar(fid):
            if f["mimeType"] == "application/vnd.google-apps.folder" and nivel < 3:
                recoger_compartida(f["id"], nivel + 1)
            elif es_medio(f):
                medios[("*", f["name"])] = (int(f.get("size", 0)), descargador(f["id"]))

    docs, medios = [], {}
    for sub in listar(folder_id):
        if sub["mimeType"] != "application/vnd.google-apps.folder":
            continue
        if norm_key(sub["name"]) == CARPETA_COMPARTIDA:
            recoger_compartida(sub["id"])
            continue
        persona = sub["name"]
        for f in listar(sub["id"]):
            mod = datetime.fromisoformat(f["modifiedTime"].replace("Z", "+00:00"))
            if f["mimeType"] == "application/vnd.google-apps.document":
                data = svc.files().export(fileId=f["id"], mimeType="text/plain").execute()
                docs.append((persona, f["name"], data.decode("utf-8"), mod))
            elif es_medio(f):
                medios[(persona, f["name"])] = (int(f.get("size", 0)), descargador(f["id"]))
    return docs, medios


# ---------- HTML ----------
def nav_html(root, activa=""):
    items = [f'<li><a href="{root}index.html"{" class=active" if not activa else ""}>Portada</a></li>']
    for s in SECCIONES:
        cls = " class=active" if s == activa else ""
        items.append(f'<li><a href="{root}seccion/{slugify(s)}.html"{cls}>{esc(s)}</a></li>')
    return "\n".join(items)


def pagina(titulo, cuerpo, root="", activa=""):
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} — XYZ Sevilla</title><link rel="stylesheet" href="{root}styles.css"></head>
<body>
<header class="site-header"><div class="container">
<div class="header-top"><div class="date" id="fecha"></div>
<a href="{root}index.html" class="logo">XYZ Sevilla<small>Periódico digital</small></a>
<div class="header-actions"><button class="burger" aria-label="Menú" aria-expanded="false">☰</button></div></div></div>
<nav class="main-nav"><div class="container"><ul>{nav_html(root, activa)}</ul></div></nav></header>
<main class="container">{cuerpo}</main>
<footer class="site-footer"><div class="container"><h4>XYZ Sevilla</h4>
<p>Proyecto universitario. Contenido elaborado por el equipo.</p>
<p class="copy">© {datetime.now().year} XYZ Sevilla. Trabajo académico.</p></div></footer>
<script src="{root}script.js"></script></body></html>"""


def figura(a, root, ratio=""):
    if a["imagen"]:
        return f'<figure class="ph {ratio}"><img src="{root}img/{a["imagen"]}" alt="{esc(a["titulo"])}" loading="lazy"></figure>'
    return f'<figure class="ph {ratio}"><span>{esc(a["seccion"])}</span></figure>'


def tarjeta(a, root, size="md", con_img=True, ratio="r-4x3", entradilla=False):
    img = figura(a, root, ratio) if con_img else ""
    sub = f'<p class="sub">{esc(a["entradilla"])}</p>' if entradilla and a["entradilla"] else ""
    return (f'<article>{img}'
            f'<span class="kicker" style="margin-top:8px">{esc(a["seccion"])}{" · 🎧 Audio" if a.get("audio") else ""}</span>'
            f'<h3 class="title {size}"><a href="{root}noticia/{a["slug"]}.html">{esc(a["titulo"])}</a></h3>'
            f'{sub}<p class="author">{esc(a["autor"])}</p></article>')


def home(arts):
    if not arts:
        return pagina("Portada", "<p style='padding:40px 0'>Aún no hay noticias publicadas.</p>")
    destacada = next((a for a in arts if a["destacada"]), arts[0])
    resto = [a for a in arts if a is not destacada]
    lat, med = resto[0:2], resto[2:4]
    hero = (f'<section class="block"><div class="grid hero"><article>{figura(destacada, "")}'
            f'<span class="kicker" style="margin-top:12px">{esc(destacada["seccion"])}</span>'
            f'<h2 class="title xl"><a href="noticia/{destacada["slug"]}.html">{esc(destacada["titulo"])}</a></h2>'
            f'<p class="sub">{esc(destacada["entradilla"])}</p><p class="author">{esc(destacada["autor"])}</p></article>'
            f'<div class="col-stack">{"".join(tarjeta(a, "", "lg", False, entradilla=True) for a in lat)}</div>'
            f'<div class="col-stack">{"".join(tarjeta(a, "", "md", True) for a in med)}</div></div></section>')
    usados = {id(destacada), *map(id, lat), *map(id, med)}
    bloques = ""
    for s in SECCIONES:
        de = [a for a in arts if a["seccion"] == s and id(a) not in usados][:4]
        if de:
            bloques += (f'<section class="block"><h2 class="section-title">{esc(s)} '
                        f'<a href="seccion/{slugify(s)}.html">Ver sección</a></h2>'
                        f'<div class="grid cols-4">{"".join(tarjeta(a, "") for a in de)}</div></section>')
    con_audio = [a for a in arts if a.get("audio")][:4]
    if con_audio:
        bloques += ('<section class="block"><h2 class="section-title">Podcast</h2>'
                    f'<div class="grid cols-4">{"".join(tarjeta(a, "") for a in con_audio)}</div></section>')
    ult = "".join(f'<li><a href="noticia/{a["slug"]}.html">{esc(a["titulo"])}</a></li>' for a in arts[:10])
    ultimas = f'<section class="block most-read"><h2 class="section-title">Lo más reciente</h2><ol>{ult}</ol></section>'
    return pagina("Noticias de Sevilla, Andalucía y España", hero + bloques + ultimas)


def pagina_seccion(s, arts):
    de = [a for a in arts if a["seccion"] == s]
    cuerpo = f'<section class="block"><h2 class="section-title">{esc(s)}</h2>'
    cuerpo += (f'<div class="grid cols-3">{"".join(tarjeta(a, "../", "lg", True, "r-4x3", True) for a in de)}</div>'
               if de else "<p>Aún no hay noticias en esta sección.</p>") + "</section>"
    return pagina(s, cuerpo, "../", s)


def pagina_noticia(a):
    parrafos = "".join(f"<p>{esc(p).replace(chr(10), '<br>')}</p>" for p in re.split(r"\n\s*\n", a["cuerpo"]) if p.strip())
    cred = f'<figcaption>{esc(a["credito"])}</figcaption>' if a["credito"] else ""
    fecha = a["fecha"].strftime("%d/%m/%Y")
    audio = (f'<div class="audio-box"><span class="kicker">Escucha esta noticia</span>'
             f'<audio controls preload="none" src="../audio/{a["audio"]}"></audio></div>') if a.get("audio") else ""
    cuerpo = (f'<article class="block" style="max-width:760px;margin:0 auto"><span class="kicker">'
              f'<a href="../seccion/{slugify(a["seccion"])}.html">{esc(a["seccion"])}</a></span>'
              f'<h1 class="title xl">{esc(a["titulo"])}</h1><p class="sub">{esc(a["entradilla"])}</p>'
              f'<p class="author">{esc(a["autor"])} · {fecha}</p><div style="margin:16px 0">{figura(a, "../")}{cred}</div>{audio}'
              f'<div style="font-family:var(--serif);font-size:18px;line-height:1.6;display:grid;gap:14px">{parrafos}</div></article>')
    return pagina(a["titulo"], cuerpo, "../", a["seccion"])


# ---------- Principal ----------
def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--local")
    g.add_argument("--drive", action="store_true")
    args = ap.parse_args()

    if args.drive:
        for var in ("GOOGLE_SERVICE_ACCOUNT_JSON", "DRIVE_FOLDER_ID"):
            if not os.environ.get(var, "").strip():
                sys.exit(f"ERROR: el secreto {var} está vacío o no existe. Créalo en Settings > Secrets and variables > Actions > Repository secrets.")
    docs, medios = leer_local(args.local) if args.local else leer_drive(os.environ["DRIVE_FOLDER_ID"].strip())

    arts, errores, slugs = [], [], set()
    for persona, nombre, texto, mod in docs:
        a, err = parse_doc(texto, persona, nombre, mod)
        if err == "BORRADOR":
            continue
        if err:
            errores.append(f"[{persona}] «{nombre}»: {err}")
            continue
        base = slugify(a["titulo"]); slug, n = base, 2
        while slug in slugs:
            slug, n = f"{base}-{n}", n + 1
        slugs.add(slug); a["slug"] = slug
        a["imagen"] = a["audio"] = ""

        def buscar(nombre):
            return medios.get((persona, nombre)) or medios.get(("*", nombre))

        if a["imagen_nombre"]:
            m, ext = buscar(a["imagen_nombre"]), Path(a["imagen_nombre"]).suffix.lower()
            if m is None:
                errores.append(f"[{persona}] «{nombre}»: imagen '{a['imagen_nombre']}' no encontrada en tu carpeta ni en Insumos (se publica sin imagen)")
            elif ext not in IMG_EXT:
                errores.append(f"[{persona}] «{nombre}»: la imagen debe ser JPG, PNG o WEBP (se publica sin imagen)")
            elif m[0] > MAX_IMG:
                errores.append(f"[{persona}] «{nombre}»: la imagen pesa más de 2 MB (se publica sin imagen)")
            else:
                a["imagen"] = f"{slug}{ext}"
                a["_img"] = m[1]
        if a["audio_nombre"]:
            m, ext = buscar(a["audio_nombre"]), Path(a["audio_nombre"]).suffix.lower()
            if m is None:
                errores.append(f"[{persona}] «{nombre}»: audio '{a['audio_nombre']}' no encontrado en tu carpeta ni en Insumos (se publica sin audio)")
            elif ext not in AUDIO_EXT:
                errores.append(f"[{persona}] «{nombre}»: el audio debe ser MP3, M4A, WAV u OGG (se publica sin audio)")
            elif m[0] > MAX_AUDIO:
                errores.append(f"[{persona}] «{nombre}»: el audio pesa más de 25 MB (se publica sin audio)")
            else:
                a["audio"] = f"{slug}{ext}"
                a["_audio"] = m[1]
        arts.append(a)
    arts.sort(key=lambda a: a["fecha"], reverse=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "noticia").mkdir(parents=True); (OUT / "seccion").mkdir(); (OUT / "img").mkdir(); (OUT / "audio").mkdir()
    for f in ("styles.css", "script.js"):
        shutil.copy(ROOT / f, OUT / f)
    (OUT / ".nojekyll").write_text("")
    (OUT / "index.html").write_text(home(arts), encoding="utf-8")
    for s in SECCIONES:
        (OUT / "seccion" / f"{slugify(s)}.html").write_text(pagina_seccion(s, arts), encoding="utf-8")
    for a in arts:
        (OUT / "noticia" / f"{a['slug']}.html").write_text(pagina_noticia(a), encoding="utf-8")
        if a["imagen"]:
            (OUT / "img" / a["imagen"]).write_bytes(a["_img"]())
        if a["audio"]:
            (OUT / "audio" / a["audio"]).write_bytes(a["_audio"]())

    print(f"Publicadas: {len(arts)} noticias")
    informe = "Informe de errores:\n" + "\n".join(f"  - {e}" for e in errores) if errores else "Sin errores."
    print(informe)
    (ROOT / "informe.txt").write_text(informe + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
