"""Genera el kit del participante: una página HTML por pieza, sus PDFs y el ZIP.

Uso:  python3 scripts/build_kit.py
Requiere Google Chrome instalado (para imprimir los PDFs).
"""
import csv
import html
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "kit"
DL = KIT / "descargas"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SITE = "psolenny.github.io/primeros-pasos-con-IA-ppt"
ZIP_NAME = "kit-participante-pon-la-ia-a-trabajar.zip"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700'
         '&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">')

FIRMA = ('<div class="firma"><b>Solenny Peralta</b>'
         '<span>Gerente de Proyectos de Innovación y Servicios TI</span></div>')

# (slug, número, título de pestaña, título, descripción, pdf)
PAGES = [
    ("glosario",  "01", "Glosario",          "Glosario de bolsillo",           "Las trece palabras que necesitas para entender cualquier conversación sobre IA en el trabajo.", "01-glosario.pdf"),
    ("plantilla", "02", "Plantilla",         "Plantilla de prompt",            "Las seis piezas de un buen prompt, para llenar. Mientras más importante la tarea, más piezas conviene usar.", "02-plantilla-de-prompt.pdf"),
    ("prompts",   "03", "Banco de prompts",  "Banco de prompts para el trabajo", "Listos para copiar. Cambia lo que está en [corchetes rosa] y pégalo en tu asistente.", "03-banco-de-prompts.pdf"),
    ("mapa",      "04", "Mapa",              "Mapa de tu primera tarea",       "Elige bien la primera tarea y ya ganaste la mitad. Una buena candidata cumple los cuatro criterios.", "04-mapa-primera-tarea.pdf"),
    ("seguridad", "05", "Seguridad",         "Checklist de seguridad",         "Antes de pegar algo en la IA, y antes de usar lo que te devolvió.", "05-checklist-seguridad.pdf"),
    ("frases",    "06", "Frases",            "Frases que sí funcionan",        "“Hazlo mejor” no dice qué está mal ni cómo se ve bien. Estas sí.", "06-frases-que-funcionan.pdf"),
    ("reglas",    "07", "Reglas y proyectos", "Reglas globales y proyectos",    "Deja escrito lo que repites: una vez en las reglas globales de tu IA, y una vez por tema en un proyecto. Paso a paso para Claude, ChatGPT, Gemini y Copilot.", "07-reglas-y-proyectos.pdf"),
]

# ---------------------------------------------------------------- contenido
GLOSARIO = [
    ("empresa", "Quien construye la IA.", "Anthropic · OpenAI · Google"),
    ("modelo", "El “cerebro” entrenado. Es el motor.", "Claude Opus · GPT · Gemini"),
    ("asistente / agente", "Modelo + instrucciones + herramientas, listo para una tarea. El chat responde; el agente actúa.", "Claude · ChatGPT · un bot de atención"),
    ("interfaz", "Por donde lo usas.", "web · escritorio · móvil · Excel · WhatsApp"),
    ("herramienta", "Lo que le permite hacer cosas, no solo hablar.", "buscar · leer un PDF · enviar un correo"),
    ("prompt", "Lo que le escribes. La primera fuente de contexto.", "“Resume este correo en 3 viñetas”"),
    ("contexto", "Todo lo que la IA tiene sobre la mesa al responder: lo que escribes, lo que le das a leer y sus instrucciones.", "mismo modelo + mejor contexto = mejor resultado"),
    ("alucinación", "Cuando la IA inventa un dato, cita o fuente con total seguridad.", "regla: todo dato se verifica"),
    ("prompt injection", "Órdenes escondidas en un texto que la IA lee y que puede obedecer.", "el CV con letra blanca"),
    ("proyecto", "Un espacio para un tema de trabajo con sus propias instrucciones y archivos. Cada chat que abres dentro ya arranca con ese contexto.", "“Correos a clientes” · “Reportes de ventas”"),
    ("skill", "Un manual de procedimiento (instrucciones + plantillas + ejemplos) que el asistente carga cuando la tarea lo pide.", "minutas · informes · propuestas"),
    ("rutina", "Una tarea que el asistente hace igual cada vez, a demanda o programada.", "“resumen de mi lunes”"),
    ("ventana de contexto", "La memoria de trabajo de una conversación. Tiene fondo: lo del medio se diluye.", "un chat por tema"),
]

PLANTILLA = [
    ("1", "Contexto", "Quién eres, para quién es, por qué.", "Soy… / Esto es para… / Lo necesito porque…"),
    ("2", "Tarea", "Qué necesitas, con un verbo claro.", "Escribe / Resume / Compara / Arma…"),
    ("3", "Insumos", "Los datos o archivos a usar.", "Usa este Excel / este correo / estas notas…"),
    ("4", "Formato", "Cómo quieres la respuesta.", "Tabla / correo / 5 viñetas / 1 página…"),
    ("5", "Criterio de calidad", "Cómo sabrás que está bien.", "Está bien si… / Debe incluir…"),
    ("6", "Límites", "Qué no hacer, tono, extensión.", "Máximo … palabras / Tono … / No menciones…"),
]

# (categoría, título, texto con [marcadores])
PROMPTS = [
    ("correo", "Responder un correo difícil",
     "Soy [tu rol] en [área]. Te pego un correo de [cliente / proveedor / colega] que [reclama / pide / se queja de]. "
     "Redacta una respuesta que [objetivo: calmar, cerrar el tema, pedir más información]. Tono profesional y cercano. "
     "Máximo 120 palabras. No prometas nada que no esté en mis notas. Dame 2 versiones.\n\n"
     "Correo recibido:\n[pega el correo]\n\nMis notas:\n[qué sí puedes ofrecer y qué no]"),
    ("reuniones", "Minuta a partir de notas",
     "Convierte estas notas de reunión en una minuta con: 1) asistentes, 2) temas tratados, 3) decisiones tomadas, "
     "4) tabla de acuerdos con responsable y fecha, 5) pendientes sin dueño. Usa solo lo que está en las notas; si falta "
     "un responsable o una fecha, márcalo como \"por definir\". Máximo 1 página.\n\n"
     "Reunión: [nombre y fecha]\nNotas:\n[pega tus notas]"),
    ("reuniones", "Preparar una reunión",
     "Tengo una reunión con [quién] sobre [tema] el [día]. Mi objetivo es [qué quiero lograr]. "
     "Prepárame: 1) una agenda de 30 minutos, 2) las 3 preguntas que debo hacer, 3) las objeciones que probablemente "
     "escuche y cómo responderlas, 4) qué información debo llevar. Pregúntame lo que falte antes de asumir."),
    ("documentos", "Resumir un documento largo",
     "Resume este documento para [quién lo va a leer: mi jefe, el equipo, un cliente] que tiene 5 minutos. "
     "Formato: 3 ideas principales en viñetas, luego riesgos o decisiones pendientes, luego \"qué necesitan de mí\". "
     "No agregues información que no esté en el documento. Si algo es ambiguo, dilo.\n\n"
     "Documento:\n[pega el texto o adjunta el archivo]"),
    ("datos", "Analizar una tabla de Excel",
     "Te adjunto una tabla de [ventas / tickets / inventario] con las columnas [lista las columnas]. Dime: "
     "1) los 3 hallazgos más importantes, 2) qué se sale de lo normal, 3) qué preguntas haría un gerente al ver esto. "
     "Muestra los números que respaldan cada hallazgo. No inventes datos que no estén en la tabla.\n\n"
     "[adjunta el archivo o pega las filas]"),
    ("datos", "Explicar o crear una fórmula de Excel",
     "Necesito una fórmula de Excel que [qué debe calcular]. Mis datos están en [columnas y rango, ej. A2:D200]. "
     "Dame la fórmula, explícame qué hace cada parte en una línea, y un ejemplo con 2 filas para comprobarla a mano. "
     "Si hay una forma más simple con una tabla dinámica, dímelo."),
    ("comunicación", "Comunicado interno",
     "Soy [rol]. Escribe un comunicado interno para [destinatarios] anunciando [qué cambia]. Estructura: qué cambia, "
     "desde cuándo, qué tienen que hacer ellos, a quién preguntar. Tono institucional: directo, claro, respetuoso, "
     "sin tecnicismos. Máximo 200 palabras.\n\nDatos clave:\n[fecha, responsable, detalles]"),
    ("comunicación", "Revisar un texto antes de enviarlo",
     "Revisa este texto que voy a enviar a [quién]. No lo reescribas completo: dame una lista de 1) errores de "
     "ortografía o gramática, 2) frases confusas y cómo aclararlas, 3) algo que pueda sonar mal o malinterpretarse. "
     "Mantén mi tono.\n\nTexto:\n[pega el texto]"),
    ("planificación", "Priorizar mi semana",
     "Estos son mis pendientes de la semana: [lista]. Mis prioridades del trimestre son [1, 2, 3]. Organízalos en una "
     "tabla con: tarea, prioridad (alta / media / baja), por qué, y día sugerido. Marca cuáles podría delegar o "
     "eliminar. Pregúntame si falta información antes de asumir."),
    ("procesos", "Documentar un procedimiento",
     "Te explico cómo hago [proceso] paso a paso: [descríbelo como se lo contarías a un compañero nuevo]. "
     "Conviértelo en un procedimiento con: objetivo, quién lo hace, pasos numerados, qué puede salir mal en cada paso "
     "y cómo verificar que quedó bien. Pregúntame lo que no quede claro antes de escribirlo."),
    ("propuestas", "Preparar una propuesta o justificación",
     "Necesito justificar [compra / proyecto / cambio] ante [quién decide]. Problema actual: [describe]. "
     "Lo que propongo: [describe]. Costo aproximado: [monto]. Arma una propuesta de 1 página con: problema, propuesta, "
     "beneficios medibles, riesgos de no hacerlo y próximos pasos. Dame además las 3 objeciones más probables y cómo "
     "responderlas."),
    ("aprender", "Entender algo nuevo rápido",
     "Explícame [tema] como a alguien de [tu área] que no es técnico. Primero en 3 frases, luego con una analogía del "
     "trabajo diario, luego los 3 errores más comunes al empezar. Al final, dime qué debería preguntar para "
     "profundizar. Si no estás seguro de algo, dilo."),
    ("verificar", "Hacer que se revise a sí misma",
     "Revisa tu respuesta anterior. Marca cada dato, cifra, nombre o cita como: ✓ viene de lo que te di, "
     "? es una suposición tuya, ✗ no tienes forma de saberlo. Luego dame la lista de lo que yo debería verificar "
     "antes de usarla."),
    ("instrucciones", "Crear tus instrucciones permanentes",
     "Voy a usarte seguido para mi trabajo. Soy [rol] en [empresa / área]. Mis tareas más comunes son [lista]. "
     "Prefiero respuestas [cortas / en tablas / en español neutro]. Nunca [inventes datos / uses tecnicismos / etc.]. "
     "Escríbeme un texto de instrucciones (máximo 150 palabras) que pueda pegar en un proyecto de mi asistente para "
     "no repetir esto cada vez."),
]

CRITERIOS = [("repetitiva", "Cada día o cada semana."), ("digital", "Correos, Excel, PDFs, sistemas."),
             ("verificable", "Sabes reconocer rápido si quedó bien."), ("bajo riesgo", "Un error no cuesta dinero ni clientes.")]
MAPA_COLS = ["Tarea", "Frecuencia", "Tiempo que toma", "Insumos", "Resultado esperado", "Quién revisa"]
MAPA_EJ = ["Resumen semanal de pendientes", "Semanal", "1 h", "Correos + notas", "1 página con prioridades", "Yo"]

SEG_ANTES = ["¿Revisé en la configuración si mis conversaciones se usan para entrenar el modelo?",
             "¿Hay datos de clientes, empleados o proveedores? Anonimízalos.",
             "¿Hay contraseñas, claves o números de cuenta? Nunca.",
             "¿Le di más permisos de los que necesita la tarea?",
             "¿El documento que va a leer viene de un tercero? Puede traer órdenes escondidas."]
SEG_DESPUES = ["¿Verifiqué cada dato, cifra, cita y fuente?",
               "¿Alguien lo revisa antes de que salga a un cliente, un pago o una decisión?",
               "¿Tiene consecuencias legales o de RR.HH.? La IA asiste, la persona decide.",
               "¿Revisarlo me tomó más que hacerlo? Entonces no era la herramienta."]

FRASES = [
    ("extensión", "Es muy largo: déjalo en 3 párrafos.", "En vez de “hazlo más corto”."),
    ("tono", "Suena a robot: escríbelo como se lo dirías a un colega.", "En vez de “más natural”."),
    ("falta algo", "Falta la fecha de entrega en el primer párrafo.", "Dile qué y dónde."),
    ("sobra algo", "Quita la parte de las excusas; ve directo a la solución.", "Lo que quitas importa tanto como lo que pides."),
    ("estructura", "Ponlo en una tabla con columnas: tarea, responsable, fecha.", "Nombra las columnas."),
    ("opciones", "Dame 2 versiones: una formal y una más cálida.", "Comparar es más fácil que describir."),
    ("enfoque", "Céntrate solo en el riesgo de costos; lo demás no importa ahora.", "Le quitas ruido."),
    ("fuentes", "Marca qué partes vienen de mi documento y cuáles son tuyas.", "Tu antídoto contra la alucinación."),
    ("antes de asumir", "Si te falta información, pregúntame antes de responder.", "Evita que rellene huecos inventando."),
    ("nivel", "Explícalo para alguien que no es técnico, con un ejemplo del trabajo.", "Define a quién le habla."),
]


# ---------------------------------------------------------------- helpers
e = html.escape


def mark(text):
    """Escapa y pinta en rosa los [marcadores]."""
    out, buf, inside = [], "", False
    for ch in text:
        if ch == "[" and not inside:
            out.append(e(buf)); buf, inside = "[", True
        elif ch == "]" and inside:
            out.append("<i>" + e(buf + "]") + "</i>"); buf, inside = "", False
        else:
            buf += ch
    out.append(e(buf))
    return "".join(out)


def page(slug, title, body, active=None, desc=""):
    tabs = "".join(
        f'<a href="{p[0]}.html" class="{"on" if p[0] == active else ""}"><span class="k">{p[1]}</span>{p[2]}</a>'
        for p in PAGES)
    tabs = f'<a href="index.html" class="{"on" if active == "index" else ""}"><span class="k">00</span>Inicio</a>' + tabs
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)} · Kit del participante</title>
<meta name="description" content="{e(desc)}">
<link rel="icon" href="../assets/logo-cecomsa-color.png">
{FONTS}
<link rel="stylesheet" href="../assets/site.css">
</head>
<body>
<div class="marq" aria-hidden="true"><div class="marq-track"><span>· kit del participante · pon la ia a trabajar por ti · contexto · especificidad · verificación </span><span>· kit del participante · pon la ia a trabajar por ti · contexto · especificidad · verificación </span></div></div>
<header class="top"><div class="wrap">
  <a href="../index.html"><img src="../assets/logo-cecomsa-color.png" alt="CECOMSA"></a>
  <nav><a href="../index.html">La charla</a><a href="../presentacion.html">Slides</a><a href="index.html" class="on">Kit</a></nav>
</div></header>
<nav class="tabs" aria-label="Piezas del kit"><div class="wrap">{tabs}</div></nav>
<main>
{body}
</main>
<footer class="foot"><div class="wrap">
  <img src="../assets/logo-cecomsa-color.png" alt="CECOMSA">
  {FIRMA}
</div></footer>
<script>
document.querySelectorAll('.copy').forEach(function(b){{b.addEventListener('click',function(){{
  var t=b.closest('.prompt').querySelector('pre').innerText;
  navigator.clipboard.writeText(t).then(function(){{b.textContent='¡copiado!';b.classList.add('ok');setTimeout(function(){{b.textContent='copiar';b.classList.remove('ok');}},1500);}});
}});}});
document.querySelectorAll('.filter button').forEach(function(b){{b.addEventListener('click',function(){{
  document.querySelectorAll('.filter button').forEach(function(x){{x.classList.toggle('on',x===b);}});
  var c=b.dataset.c;document.querySelectorAll('.prompt').forEach(function(p){{p.style.display=(c==='todas'||p.dataset.c===c)?'':'none';}});
}});}});
</script>
</body>
</html>
"""


WORKSHOP_BOX = """<a class="box negro" href="https://forms.cloud.microsoft/r/4RbmgTepT5" target="_blank" rel="noopener" style="margin-top:40px">
  <span class="n">// workshop · 21 de noviembre · 3 horas · 20 lugares</span>
  <h3>Tu primera tarea resuelta con IA de principio a fin.</h3>
  <p style="color:rgba(255,255,255,.85)">100% práctico. Trae laptop, tu IA instalada y tu mapa lleno. Inscríbete →</p>
</a>"""


def piece(i):
    slug, n, tab, title, desc, pdf = PAGES[i]
    prev_ = PAGES[i - 1] if i > 0 else None
    next_ = PAGES[i + 1] if i < len(PAGES) - 1 else None
    pager = '<div class="pager">'
    pager += f'<a class="chip" href="{prev_[0]}.html">← {prev_[1]} · {prev_[2]}</a>' if prev_ else '<a class="chip" href="index.html">← Inicio del kit</a>'
    pager += f'<a class="chip p" href="{next_[0]}.html">{next_[1]} · {next_[2]} →</a>' if next_ else '<a class="chip p" href="index.html">Volver al inicio del kit →</a>'
    pager += '</div>'
    pager = WORKSHOP_BOX + pager
    head = f"""<section class="hero"><div class="wrap">
  <div class="print-only print-head"><img src="../assets/logo-cecomsa-color.png" alt="CECOMSA"><span>Kit del participante · Pon la IA a trabajar por ti · Solenny Peralta</span></div>
  <div class="tag">// kit · pieza {n} de {len(PAGES):02d}</div>
  <div class="pagehead"><h1>{e(title)}</h1><a class="chip n no-print" href="descargas/{pdf}" download>↓ descargar PDF</a></div>
  <p>{e(desc)}</p>
</div></section>"""
    return head, pager


def build_glosario():
    rows = "".join(f'<div class="gl-row"><div class="gl-t">{e(t)}</div><div class="gl-d">{e(d)}</div><div class="gl-e">{e(x)}</div></div>'
                   for t, d, x in GLOSARIO)
    return f'<section class="sec"><div class="wrap"><div class="gl">{rows}</div>__PAGER__</div></section>'


def build_plantilla():
    fields = "".join(f'<div class="field"><div class="fh"><b>{n}</b><span>{e(t)}</span><small>{e(h)}</small></div>'
                     f'<textarea placeholder="{e(ph)}" aria-label="{e(t)}"></textarea></div>' for n, t, h, ph in PLANTILLA)
    ejemplo = ('<span style="color:#E31C79">[Contexto]</span> Soy coordinadora de servicio al cliente en una distribuidora. '
               '<span style="color:#E31C79">[Tarea]</span> Escribe un correo para un cliente corporativo cuyo pedido de 40 laptops llegará 5 días tarde por un retraso en aduanas. '
               '<span style="color:#E31C79">[Criterio]</span> Objetivo: mantener la relación. '
               '<span style="color:#E31C79">[Límites]</span> Tono profesional y cercano, sin excusas largas. '
               '<span style="color:#E31C79">[Insumos]</span> Incluye: disculpa breve, nueva fecha (22 de octubre), qué estamos haciendo para que no se repita y un contacto directo. '
               '<span style="color:#E31C79">[Formato]</span> Máximo 150 palabras. Dame 2 versiones: una formal y una más cálida.')
    return f"""<section class="sec"><div class="wrap"><div class="grid g2" style="align-items:start">
  <div>{fields}</div>
  <div class="box azul"><span class="n">// ejemplo resuelto</span><p style="font-size:15.5px;line-height:1.6">{ejemplo}</p>
    <p style="margin-top:18px;font-size:14px"><b style="color:#fff">Regla de oro:</b> escríbelo como si se lo pidieras a una persona inteligente que empezó hoy.</p></div>
</div>__PAGER__</div></section>"""


def build_prompts():
    cats = []
    for c, _, _ in PROMPTS:
        if c not in cats:
            cats.append(c)
    filt = '<div class="filter no-print"><button class="on" data-c="todas">todas</button>' + "".join(
        f'<button data-c="{e(c)}">{e(c)}</button>' for c in cats) + '</div>'
    items = "".join(
        f'<div class="prompt" data-c="{e(c)}"><div class="prompt-head"><span class="prompt-n">{k:02d} · {e(c)}</span>'
        f'<span class="prompt-t">{e(t)}</span><button class="copy" type="button">copiar</button></div><pre>{mark(p)}</pre></div>'
        for k, (c, t, p) in enumerate(PROMPTS, 1))
    return f'<section class="sec"><div class="wrap">{filt}{items}__PAGER__</div></section>'


def build_mapa():
    chips = "".join(f'<div class="box soft"><span class="n">criterio {k}</span><h3>{e(t)}</h3><p>{e(d)}</p></div>'
                    for k, (t, d) in enumerate(CRITERIOS, 1))
    th = "".join(f"<th>{e(c)}</th>" for c in MAPA_COLS)
    ex = "".join(f"<td>{e(c)}</td>" for c in MAPA_EJ)
    blank = "<tr>" + "<td></td>" * len(MAPA_COLS) + "</tr>"
    return f"""<section class="sec"><div class="wrap">
  <div class="grid g4">{chips}</div>
  <h2 style="margin-top:40px;font-size:26px">Tu mapa</h2>
  <p class="lead">La primera fila es un ejemplo. Llena las demás con tareas reales.</p>
  <div class="scroll"><table class="tbl"><tr>{th}</tr><tr class="ex">{ex}</tr>{blank * 5}</table></div>
  <div class="box negro" style="margin-top:30px"><span class="n">// el orden importa</span><h3>Primero optimizar, después automatizar.</h3>
  <p style="color:rgba(255,255,255,.85)">Optimizar es que la IA lo haga contigo, más rápido, y tú revisas. Automatizar es que lo haga sola. Llega ahí solo cuando ya confías en el resultado.</p></div>
  <p class="lead no-print" style="margin-top:22px">¿Prefieres llenarlo en Excel? Descarga <a href="descargas/mapa-primera-tarea.csv" download>mapa-primera-tarea.csv</a>.</p>
  __PAGER__</div></section>"""


def build_seguridad():
    a = "".join(f"<li>{e(x)}</li>" for x in SEG_ANTES)
    d = "".join(f"<li>{e(x)}</li>" for x in SEG_DESPUES)
    return f"""<section class="sec"><div class="wrap"><div class="grid g2" style="align-items:start">
  <div class="box"><span class="n">// antes de enviar</span><h3>Lo que le das</h3><ul class="check" style="margin-top:14px">{a}</ul></div>
  <div class="box azul"><span class="n">// antes de usar el resultado</span><h3>Lo que te devuelve</h3><ul class="check" style="margin-top:14px">{d}</ul></div>
</div>
<div class="box negro" style="margin-top:28px"><span class="n">// la regla general</span><h3>La IA propone. Una persona revisa.</h3>
<p style="color:rgba(255,255,255,.85)">Sobre todo antes de que algo salga hacia un cliente, un pago o una decisión.</p></div>
__PAGER__</div></section>"""


def build_frases():
    half = len(FRASES) // 2
    col = lambda xs: "".join(f'<div class="phr"><b>{e(k)}</b><q>{e(q)}</q><small>{e(s)}</small></div>' for k, q, s in xs)
    return f"""<section class="sec"><div class="wrap"><div class="grid g2" style="align-items:start">
  <div>{col(FRASES[:half])}</div><div>{col(FRASES[half:])}</div></div>
  <div class="box rosa" style="margin-top:24px"><span class="n">// la idea</span><h3>Cuanto más específica la crítica, más útil la corrección.</h3></div>
  __PAGER__</div></section>"""


REGLAS_GLOBALES = """Soy [tu nombre], [tu rol] en [tu área]. Trabajo en [tipo de empresa].
Respóndeme siempre en español, de forma directa y breve. Prefiero tablas y viñetas antes que párrafos largos.
Si te falta información para responder bien, pregúntame antes de asumir.
Nunca inventes datos, cifras, nombres ni fuentes: si no lo sabes, dilo.
Cuando te pida un correo, usa un tono profesional y cercano, sin excusas largas."""

REGLAS_PROYECTO = """Este proyecto es para [el tema: ej. correos a clientes de la distribuidora].
Mi rol aquí: [ej. coordinadora de servicio al cliente].
Quién recibe lo que producimos: [ej. clientes corporativos, mi jefe, el equipo].
Formato que uso siempre: [ej. correos de máximo 150 palabras con asunto, saludo, 2 párrafos y cierre].
Reglas de este tema: [ej. nunca prometer fechas sin confirmar con logística; firmar con mi nombre y cargo].
Archivos de referencia: [ej. plantilla de correo aprobada, lista de precios vigente] (los adjunto al proyecto)."""

# (herramienta, dónde van las reglas globales, pasos globales, cómo se llama el "proyecto", pasos proyecto, nota)
HERRAMIENTAS = [
    ("Claude", "Preferencias del perfil",
     ["Clic en tus iniciales (abajo a la izquierda) → Configuración.",
      "Busca el campo de preferencias personales (“qué debe tener en cuenta Claude al responder”).",
      "Pega tus reglas globales y guarda. Aplican a todos los chats nuevos."],
     "Proyecto",
     ["En el menú lateral, Proyectos → Crear proyecto. Ponle el nombre del tema.",
      "Abre el proyecto → Instrucciones del proyecto → pega las reglas del proyecto.",
      "En Archivos del proyecto, sube tus plantillas y documentos de referencia.",
      "Todo chat que abras dentro del proyecto arranca con esas instrucciones y archivos."],
     "Los proyectos requieren plan de pago. Las preferencias del perfil están en todos los planes."),
    ("ChatGPT", "Personalización → Instrucciones personalizadas",
     ["Clic en tu foto → Configuración → Personalización.",
      "Activa “Habilitar personalización” y abre Instrucciones personalizadas.",
      "Pega tus reglas globales en el campo de cómo quieres que responda y guarda. Aplican a los chats nuevos."],
     "Proyecto",
     ["En el menú lateral, Proyectos → Nuevo proyecto. Ponle el nombre del tema.",
      "Dentro del proyecto, abre Instrucciones y pega las reglas del proyecto.",
      "Agrega archivos con el botón de archivos del proyecto.",
      "Los chats creados dentro del proyecto usan esas instrucciones y archivos."],
     "Si en tu app dice “Personalizar ChatGPT”, es la misma pantalla con el nombre viejo."),
    ("Gemini", "Instrucciones para Gemini (contexto personal)",
     ["Clic en tu foto o en Configuración → busca Instrucciones para Gemini / Contexto personal.",
      "Pega tus reglas globales y guarda.",
      "Si no aparece en tu cuenta, usa un Gem como se explica abajo."],
     "Gem",
     ["En el menú lateral, Explorar Gems → Nuevo Gem. Ponle el nombre del tema.",
      "En Instrucciones, pega las reglas del proyecto (la varita puede ayudarte a redactarlas).",
      "En Conocimiento, agrega archivos desde tu equipo o Google Drive.",
      "Guarda. Cada vez que abras ese Gem, arranca con esas instrucciones."],
     "Los Gems están disponibles en los planes gratuitos y de pago."),
    ("Microsoft 365 Copilot", "Personalización → Instrucciones personalizadas",
     ["En la app de Copilot, Configuración → Personalización → Instrucciones personalizadas.",
      "Pega tus reglas globales y guarda."],
     "Notebook de Copilot",
     ["Crea un Notebook de Copilot para el tema y agrégale tus archivos.",
      "En el menú del notebook, elige Instrucciones de Copilot y pega las reglas del proyecto.",
      "Todo lo que preguntes dentro del notebook usa esos archivos e instrucciones."],
     "Requiere licencia de Microsoft 365 Copilot. Si compartes el notebook, los demás ven tus instrucciones."),
]


def build_reglas():
    pasos = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    tabs = "".join(f"""<div class="box">
  <span class="n">// {e(nombre)}</span>
  <div class="grid g2" style="gap:14px;margin-top:6px">
    <div><h4 style="font-size:15px;margin-bottom:6px">Reglas globales · {e(donde)}</h4><ol style="margin-left:18px;font-size:14.5px;line-height:1.5">{pasos(pg)}</ol></div>
    <div><h4 style="font-size:15px;margin-bottom:6px">Por tema · {e(proy)}</h4><ol style="margin-left:18px;font-size:14.5px;line-height:1.5">{pasos(pp)}</ol></div>
  </div>
  <p style="font-size:13.5px;color:var(--muted);margin-top:10px">{e(nota)}</p>
</div>""" for nombre, donde, pg, proy, pp, nota in HERRAMIENTAS)
    return f"""<section class="sec"><div class="wrap">
  <div class="grid g2" style="align-items:start">
    <div class="box azul"><span class="n">// nivel 1 · reglas globales</span><h3>Lo que debe saber siempre</h3>
      <p style="color:rgba(255,255,255,.85)">Quién eres, cómo te gusta que te responda y qué nunca debe hacer. Se escribe una vez y aplica a todos los chats. Máximo 10 líneas.</p></div>
    <div class="box negro"><span class="n">// nivel 2 · un proyecto por tema</span><h3>Lo que aplica a un tema</h3>
      <p style="color:rgba(255,255,255,.85)">El formato, las reglas y los archivos de un tema de trabajo. Cada chat nuevo dentro del proyecto ya arranca con eso. Un proyecto por tema, un chat por tarea.</p></div>
  </div>
  <div class="box soft" style="margin-top:28px"><span class="n">// mi proyecto · checklist de manos a la obra</span>
    <h3>Tu proyecto vive en tu IA, no en papel</h3>
    <ul class="check" style="margin-top:12px">
      <li>Creé el proyecto (Claude/ChatGPT: Proyecto · Gemini: Gem · Copilot: Notebook) con el nombre de mi tarea.</li>
      <li>Pegué las instrucciones del proyecto y llené los [corchetes] con lo que escribí en mi hoja.</li>
      <li>Subí al menos un archivo de referencia (plantilla, lista, ejemplo).</li>
      <li>Corrí un prompt del banco dentro del proyecto.</li>
      <li>Lo corregí una vez con una frase específica.</li>
    </ul></div>
  <h2 style="margin-top:40px;font-size:26px">Plantillas para copiar</h2>
  <p class="lead">Cambia lo que está en [corchetes]. Pega la primera en las reglas globales; la segunda, en cada proyecto que crees.</p>
  <div class="prompt"><div class="prompt-head"><span class="prompt-n">global</span><span class="prompt-t">Reglas globales</span><button class="copy" type="button">copiar</button></div><pre>{mark(REGLAS_GLOBALES)}</pre></div>
  <div class="prompt"><div class="prompt-head"><span class="prompt-n">proyecto</span><span class="prompt-t">Instrucciones de un proyecto</span><button class="copy" type="button">copiar</button></div><pre>{mark(REGLAS_PROYECTO)}</pre></div>
  <h2 style="margin-top:40px;font-size:26px">Dónde se pone, en cada IA</h2>
  <p class="lead">Los menús cambian de nombre con frecuencia; si el tuyo se ve distinto, busca “instrucciones” o “personalización” en la configuración.</p>
  <div style="display:flex;flex-direction:column;gap:16px">{tabs}</div>
  <div class="box soft" style="margin-top:28px"><span class="n">// la regla de las tres veces</span><h3>¿Va en global, en proyecto o en el chat?</h3>
    <ul style="margin:8px 0 0 18px;font-size:15.5px;line-height:1.6">
      <li><b>Lo escribiste en un chat una vez:</b> queda en el chat.</li>
      <li><b>Lo repites en varios chats del mismo tema:</b> va al proyecto.</li>
      <li><b>Lo repites en todos los temas:</b> va a las reglas globales.</li>
    </ul></div>
  __PAGER__</div></section>"""


BUILDERS = [build_glosario, build_plantilla, build_prompts, build_mapa, build_seguridad, build_frases, build_reglas]


def build_index():
    cards = "".join(f'<a class="box" href="{s}.html"><span class="n">{n} · {e(tab)}</span><h3>{e(t)}</h3><p>{e(d)}</p></a>'
                    for s, n, tab, t, d, _ in PAGES)
    dls = f'<a class="dlc big" href="descargas/{ZIP_NAME}" download><span class="ext zip">ZIP</span><span><b>Descargar todo el kit</b><small>Los 7 PDFs + la hoja del participante + banco de prompts en texto + mapa en CSV</small></span></a>'
    dls += "".join(f'<a class="dlc" href="descargas/{pdf}" download><span class="ext">PDF</span><span><b>{n} · {e(t)}</b><small>{pdf}</small></span></a>'
                   for s, n, tab, t, d, pdf in PAGES)
    dls += '<a class="dlc" href="descargas/banco-de-prompts.md" download><span class="ext">MD</span><span><b>Banco de prompts en texto</b><small>para copiar sin formato</small></span></a>'
    dls += '<a class="dlc" href="descargas/mapa-primera-tarea.csv" download><span class="ext">CSV</span><span><b>Mapa de tu primera tarea</b><small>ábrelo en Excel</small></span></a>'
    body = f"""<section class="hero azul"><div class="wrap">
  <div class="tag">// kit del participante</div>
  <h1>Todo lo de la charla,<br>listo para <span class="hl">usar</span>.</h1>
  <p>Siete piezas, una por pestaña. Léelas en línea, copia los prompts con un clic o descárgalo todo en un ZIP.</p>
  <div class="meta"><a class="chip p" href="descargas/{ZIP_NAME}" download>↓ descargar todo (ZIP)</a><a class="chip" href="prompts.html">ir al banco de prompts →</a></div>
</div></section>
<section class="sec"><div class="wrap">
  <div class="eyebrow">// las piezas</div><h2>Elige por dónde empezar.</h2>
  <p class="lead">Si solo tienes cinco minutos: abre el <a href="mapa.html">mapa</a>, elige una tarea y usa un prompt del <a href="prompts.html">banco</a>.</p>
  <div class="grid g3">{cards}</div>
</div></section>
<section class="band"><div class="wrap">
  <div class="eyebrow" style="color:#E31C79">// lo que sigue · 21 de noviembre · 3 horas · 100% práctico</div>
  <p class="quote">Workshop: <em>Tu primera tarea resuelta con IA</em> de principio a fin.</p>
  <p style="color:rgba(255,255,255,.8);margin-top:14px;max-width:60ch">Trae tu mapa lleno y tu IA lista. Te vas con la tarea resuelta.</p>
</div></section>
<section class="sec" id="descargas"><div class="wrap">
  <div class="eyebrow">// descargas</div><h2>Llévatelo.</h2>
  <p class="lead">Cada pieza tiene su PDF listo para imprimir. El ZIP trae todo junto.</p>
  <div class="dl">{dls}</div>
</div></section>"""
    return page("index", "Kit del participante", body, "index", "Glosario, plantilla de prompt, banco de prompts, mapa, seguridad, frases que funcionan, y reglas globales y proyectos.")


def write_extras():
    md = ["# Banco de prompts para el trabajo", "",
          "Kit del participante · Pon la IA a trabajar por ti · Solenny Peralta", "",
          "Cambia lo que está entre [corchetes] y pégalo en tu asistente.", ""]
    for k, (c, t, p) in enumerate(PROMPTS, 1):
        md += [f"## {k:02d} · {t} ({c})", "", "```", p, "```", ""]
    (DL / "banco-de-prompts.md").write_text("\n".join(md), encoding="utf-8")
    with open(DL / "mapa-primera-tarea.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(MAPA_COLS); w.writerow(MAPA_EJ)
        for _ in range(9):
            w.writerow([""] * len(MAPA_COLS))


def print_pdfs():
    for slug, *_rest in PAGES:
        pdf = _rest[-1]
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=4000", f"--print-to-pdf={DL / pdf}",
                        (KIT / f"{slug}.html").as_uri()],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def make_zip():
    leeme = ("Kit del participante · Pon la IA a trabajar por ti\n"
             "Solenny Peralta · Gerente de Proyectos de Innovación y Servicios TI\n\n"
             "Contenido:\n" + "".join(f"  {p[5]}  {p[3]}\n" for p in PAGES) +
             "  hoja-participante.pdf  La hoja de la charla, para imprimir\n"
             "  banco-de-prompts.md  Los prompts en texto plano, para copiar\n"
             "  mapa-primera-tarea.csv  El mapa para llenar en Excel\n\n"
             f"Versión en línea: https://{SITE}/kit/\n")
    with zipfile.ZipFile(DL / ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("kit-participante/LEEME.txt", leeme)
        for p in PAGES:
            z.write(DL / p[5], f"kit-participante/{p[5]}")
        hoja = ROOT / "material" / "hoja-participante.pdf"
        if hoja.exists():
            z.write(hoja, "kit-participante/hoja-participante.pdf")
        z.write(DL / "banco-de-prompts.md", "kit-participante/banco-de-prompts.md")
        z.write(DL / "mapa-primera-tarea.csv", "kit-participante/mapa-primera-tarea.csv")


def main():
    if DL.exists():
        shutil.rmtree(DL)
    DL.mkdir(parents=True)
    (KIT / "index.html").write_text(build_index(), encoding="utf-8")
    for i, b in enumerate(BUILDERS):
        slug, n, tab, title, desc, pdf = PAGES[i]
        head, pager = piece(i)
        body = head + b().replace("__PAGER__", pager)
        (KIT / f"{slug}.html").write_text(page(slug, title, body, slug, desc), encoding="utf-8")
    write_extras()
    print_pdfs()
    make_zip()
    for f in sorted(DL.iterdir()):
        print(f"{f.stat().st_size/1024:8.1f} KB  {f.name}")


if __name__ == "__main__":
    main()
