// Función de Vercel para el bot TecnoDemo del demo en vivo.
//
// Variables de entorno (en Vercel → Settings → Environment Variables):
//   ANTHROPIC_API_KEY  la clave de la API (obligatoria)
//   BOT_ENABLED        "true" para encender el bot; cualquier otro valor lo apaga
//   BOT_MODEL          opcional, por defecto claude-opus-5-5
//
// Protecciones para un enlace público: interruptor, límite por persona,
// largo máximo de mensaje y de conversación, y respuestas cortas.
import Anthropic from "@anthropic-ai/sdk";
import { NORMAL, BLINDADO } from "./_prompts.js";

const MODEL = process.env.BOT_MODEL || "claude-opus-5-5";
// La forma "default" de fallbacks aplica a estos modelos en la API de Claude.
const FALLBACK_MODELS = new Set(["claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"]);

const ALLOWED_ORIGINS = [
  "https://psolenny.github.io",
  "http://localhost:8765",
  "https://primeros-pasos-con-ia-ppt.vercel.app",
];

const MAX_CHARS = 1200;      // por mensaje del público
const MAX_TURNS = 10;        // mensajes del público por conversación
const RATE_WINDOW_MS = 10 * 60 * 1000;
// En la sala todos los celulares salen por la misma IP del Wi-Fi, así que el límite
// fino va por persona (la sesión que genera la página) y el de IP es solo un techo
// alto contra abusos. Probado con 40 personas simultáneas (3 mensajes cada una).
const RATE_MAX_SESSION = 20; // mensajes por persona cada 10 minutos
const RATE_MAX_IP = 600;     // mensajes por IP cada 10 minutos (una sala completa)

// Límite en memoria: es por instancia, así que es aproximado. Para la charla basta.
const hits = new Map();
function overLimit(key, max) {
  const now = Date.now();
  const list = (hits.get(key) || []).filter((t) => now - t < RATE_WINDOW_MS);
  list.push(now);
  hits.set(key, list);
  return list.length > max;
}

function cors(req, res) {
  const origin = req.headers.origin || "";
  if (ALLOWED_ORIGINS.includes(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

function validMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0) return false;
  if (messages.filter((m) => m.role === "user").length > MAX_TURNS) return false;
  return messages.every((m, i) =>
    m && typeof m.content === "string" && m.content.trim() &&
    m.content.length <= MAX_CHARS * 2 &&
    m.role === (i % 2 === 0 ? "user" : "assistant")) &&
    messages[messages.length - 1].role === "user" &&
    messages[messages.length - 1].content.length <= MAX_CHARS;
}

const client = new Anthropic();

export default async function handler(req, res) {
  cors(req, res);
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return res.status(405).json({ error: "Método no permitido." });

  if (process.env.BOT_ENABLED !== "true") {
    return res.status(503).json({ error: "Tecla está apagada en este momento. Vuelve durante la charla." });
  }

  const ip = (req.headers["x-forwarded-for"] || "").split(",")[0].trim() || "anon";
  const { messages, mode, session } = req.body || {};
  const sid = typeof session === "string" && /^[a-z0-9-]{8,64}$/i.test(session) ? session : null;
  if (overLimit("ip:" + ip, RATE_MAX_IP) || (sid && overLimit("s:" + sid, RATE_MAX_SESSION))) {
    return res.status(429).json({ error: "Muchos mensajes seguidos. Espera unos minutos y vuelve a intentar." });
  }

  if (!validMessages(messages)) {
    return res.status(400).json({ error: `La conversación no es válida o es muy larga (máximo ${MAX_TURNS} mensajes de ${MAX_CHARS} caracteres). Empieza una nueva.` });
  }

  const params = {
    model: MODEL,
    max_tokens: 2000,
    system: mode === "blindado" ? BLINDADO : NORMAL,
    output_config: { effort: "low" },
    messages,
  };
  if (FALLBACK_MODELS.has(MODEL)) {
    params.betas = ["server-side-fallback-2026-07-01"];
    params.fallbacks = "default";
  }

  try {
    const response = await client.beta.messages.create(params);
    if (response.stop_reason === "refusal") {
      return res.status(200).json({ reply: "(La IA se negó a responder este mensaje.)", refused: true });
    }
    const reply = response.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("\n")
      .trim();
    return res.status(200).json({ reply: reply || "(Sin respuesta.)" });
  } catch (error) {
    if (error instanceof Anthropic.RateLimitError) {
      return res.status(429).json({ error: "Hay mucha gente probando a la vez. Intenta en unos segundos." });
    }
    if (error instanceof Anthropic.AuthenticationError) {
      console.error("Clave de API inválida o ausente");
      return res.status(500).json({ error: "El bot no está configurado todavía." });
    }
    if (error instanceof Anthropic.APIError) {
      console.error(`Error de la API ${error.status}:`, error.message);
      return res.status(502).json({ error: "La IA no respondió. Intenta de nuevo." });
    }
    console.error(error);
    return res.status(500).json({ error: "Algo salió mal. Intenta de nuevo." });
  }
}
