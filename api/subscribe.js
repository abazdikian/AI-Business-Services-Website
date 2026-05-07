// Vercel serverless function: form -> Buttondown -> redirect.
//
// HTML forms POST here with: email, first_name, business_type (optional),
// one or more `tag` values, optional metadata.*, and `destination` (a
// same-origin path to redirect to on success).
//
// We call Buttondown's REST API server-side so the API key stays in the
// Vercel env (BUTTONDOWN_API_KEY), then 302 the visitor to the right
// thank-you page. No Cloudflare bot challenge, no leaked credentials.

const BUTTONDOWN_API = "https://api.buttondown.email/v1/subscribers";

// Where users go if something goes wrong, or if a malicious destination
// was passed in.
const FALLBACK_DESTINATION = "/thank-you-3-workflows";

function asArray(value) {
  if (value === undefined || value === null) return [];
  return Array.isArray(value) ? value : [value];
}

function safeDestination(raw) {
  // Only allow same-origin paths starting with a single "/" (and not "//"
  // which would let an attacker redirect to another domain).
  if (typeof raw !== "string") return FALLBACK_DESTINATION;
  if (!raw.startsWith("/") || raw.startsWith("//")) return FALLBACK_DESTINATION;
  return raw;
}

function extractMetadata(body) {
  // Form fields named "metadata.foo" map to {foo: ...} on the Buttondown side.
  const metadata = {};
  for (const [key, value] of Object.entries(body)) {
    if (key.startsWith("metadata.")) {
      metadata[key.slice("metadata.".length)] = value;
    }
  }
  return metadata;
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).send("Method not allowed");
    return;
  }

  const apiKey = process.env.BUTTONDOWN_API_KEY;
  if (!apiKey) {
    console.error("BUTTONDOWN_API_KEY missing from environment");
    res.redirect(302, FALLBACK_DESTINATION);
    return;
  }

  const body = req.body || {};
  const email = (body.email || "").trim();
  const firstName = (body.first_name || "").trim();
  const businessType = (body.business_type || "").trim();
  const tags = asArray(body.tag).filter(Boolean);
  const destination = safeDestination(body.destination);
  const metadata = extractMetadata(body);

  if (!email || !email.includes("@")) {
    // Bounce back to the form's page if we have a Referer; otherwise
    // send them to the fallback so they're not stranded.
    const back = req.headers.referer || FALLBACK_DESTINATION;
    res.redirect(302, back);
    return;
  }

  // Buttondown payload. notes captures fields not directly supported by
  // their schema (first_name, business_type) so they're searchable later.
  const noteParts = [];
  if (firstName) noteParts.push(`first_name=${firstName}`);
  if (businessType) noteParts.push(`business_type=${businessType}`);

  const payload = {
    email_address: email,
    tags,
    metadata,
    notes: noteParts.join(" · "),
    type: "regular",
  };

  try {
    const resp = await fetch(BUTTONDOWN_API, {
      method: "POST",
      headers: {
        "Authorization": `Token ${apiKey}`,
        "Content-Type": "application/json",
        "X-Buttondown-Collision-Behavior": "add",  // upsert: tag existing subs instead of erroring
      },
      body: JSON.stringify(payload),
    });

    if (!resp.ok && resp.status !== 200 && resp.status !== 201) {
      // Even on duplicate-email errors we'd rather complete the funnel
      // than show a scary error. Log details for debugging.
      const text = await resp.text();
      console.error("Buttondown API error", resp.status, text.slice(0, 500));
    }
  } catch (err) {
    console.error("Buttondown fetch threw", err);
  }

  res.redirect(302, destination);
}
