// Synchronisation automatique de la page d'accueil avec la dernière release GitHub.
// Repli vers la page /releases/latest en l'absence de connexion ou si l'API est limitée.
(function () {
  "use strict";
  const base = "https://github.com/TheDwarfy01/mon-evolution/releases";
  const api = "https://api.github.com/repos/TheDwarfy01/mon-evolution/releases/latest";
  const page = base + "/latest";
  const ids = ["download-apk", "download-apk-bottom"];
  const byId = id => document.getElementById(id);
  const link = byId("download-release");
  if (link) link.href = page;
  for (const id of ids) {
    const a = byId(id);
    if (a) a.href = page;
  }
  const status = byId("latest-version");
  if (!status) return;
  const controller = new AbortController();
  // Keep the page usable if the remote API is blocked by an extension or offline.
  const timeout = setTimeout(() => controller.abort(), 6500);
  fetch(api, {
    headers: { Accept: "application/vnd.github+json" },
    cache: "no-store",
    signal: controller.signal
  }).then(response => {
    if (!response.ok) throw new Error("GitHub API unavailable");
    return response.json();
  }).then(release => {
    const tag = typeof release.tag_name === "string" ? release.tag_name : "";
    if (!/^v\d+(?:\.\d+){1,3}$/.test(tag)) throw new Error("Invalid tag");
    const wanted = "Mon_Evolution_IMC_" + tag + ".apk";
    const asset = Array.isArray(release.assets) ? release.assets.find(a =>
      a && a.name === wanted && typeof a.browser_download_url === "string"
      && a.browser_download_url.startsWith(base + "/download/" + tag + "/")
    ) : null;
    if (!asset) throw new Error("APK missing");
    for (const id of ids) {
      const a = byId(id);
      if (a) a.href = asset.browser_download_url;
    }
    status.replaceChildren();
    status.append(document.createTextNode("Dernière version publiée : "));
    const a = document.createElement("a");
    a.href = release.html_url && release.html_url.startsWith(base + "/tag/") ? release.html_url : page;
    a.textContent = tag;
    status.append(a);
    const suffix = document.createTextNode(" · APK Android disponible");
    status.append(suffix);
  }).catch(() => {
    status.replaceChildren();
    status.append(document.createTextNode("Dernière version : "));
    const a = document.createElement("a");
    a.href = page;
    a.textContent = "vérifier sur GitHub Releases";
    status.append(a);
  }).finally(() => clearTimeout(timeout));
})();
