// This file is optional — the polling logic is already inline in index.html.
// Kept here so you can move the logic out of the HTML if you prefer.

async function pollStatus() {
  const r = await fetch('/status');
  const d = await r.json();
  console.log('Status:', d);
  return d;
}

window.pollStatus = pollStatus;