# -*- coding: utf-8 -*-
"""Envoi du digest par email via Resend."""

import html as H
import json
import os
import urllib.request

API = "https://api.resend.com/emails"

# En local, la clé Resend vit déjà dans le projet du site (tirée de Vercel).
# En CI, elle arrive par les secrets GitHub et ce bloc ne fait rien.
_LOCAL_ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "..", "site", ".env.vercel.local")
if not os.environ.get("RESEND_API_KEY") and os.path.exists(_LOCAL_ENV):
    with open(_LOCAL_ENV, encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith(("RESEND_API_KEY=", "AUDIT_FROM=")):
                cle, _, val = ligne.strip().partition("=")
                os.environ.setdefault(cle, val.strip('"'))

FROM = os.environ.get("AUDIT_FROM", "Robin Bouvet - Speerla <audit@speerlastudio.com>")
TO = os.environ.get("WATCH_TO", "audit@speerlastudio.com")


def _fenetre(offres):
    """Le nombre de devis deja deposes, traduit en verdict et en couleur."""
    if offres is None:
        return "offres inconnues", "#6b7280"
    if offres == 0:
        return "PERSONNE N'A REPONDU", "#047857"
    if offres <= 5:
        return "%d offres, fenêtre ouverte" % offres, "#047857"
    if offres <= 20:
        return "%d offres, ça se referme" % offres, "#b45309"
    return "%d offres, il faut la maquette" % offres, "#b91c1c"


def _bloc(item, brouillon):
    return """
<div style="border:1px solid #d8dde6;border-radius:10px;padding:18px 20px;margin:0 0 22px">
  <div style="font:600 12px/1 -apple-system,Segoe UI,sans-serif;color:#6b7280;letter-spacing:.06em;text-transform:uppercase">
    {score} pts &nbsp;·&nbsp; {budget} &nbsp;·&nbsp; publié il y a {age} &nbsp;·&nbsp; <span style="color:{teinte}">{fenetre}</span>
  </div>
  <h2 style="font:700 19px/1.3 -apple-system,Segoe UI,sans-serif;color:#0f172a;margin:8px 0 10px">{titre}</h2>
  <p style="font:400 14px/1.55 -apple-system,Segoe UI,sans-serif;color:#374151;margin:0 0 14px">{brief}</p>
  <p style="margin:0 0 16px">
    <a href="{url}" style="display:inline-block;background:#0f172a;color:#fff;text-decoration:none;
       font:600 14px -apple-system,Segoe UI,sans-serif;padding:10px 18px;border-radius:7px">Répondre sur Codeur</a>
  </p>
  <div style="font:600 12px -apple-system,Segoe UI,sans-serif;color:#6b7280;margin:0 0 6px">
    BROUILLON DE RÉPONSE (à relire avant envoi)</div>
  <pre style="white-space:pre-wrap;background:#f6f7f9;border-radius:8px;padding:14px;
       font:400 13px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;color:#111827;margin:0">{draft}</pre>
</div>""".format(
        score=item["score"], budget=H.escape(item["budget"]), age=item["age"],
        fenetre=_fenetre(item.get("offres"))[0], teinte=_fenetre(item.get("offres"))[1],
        titre=H.escape(item["title"]), brief=H.escape(item["body"][:600]),
        url=H.escape(item["url"]), draft=H.escape(brouillon))


def envoyer_html(sujet, html_body):
    """Brique d'envoi partagée par la veille Codeur et le radar BODACC."""
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        raise RuntimeError("RESEND_API_KEY absent de l'environnement")
    payload = json.dumps({
        "from": FROM, "to": [TO], "subject": sujet, "html": html_body,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=payload, method="POST", headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "User-Agent": "SpeerlaWatch/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def envoyer(items, brouillons):
    n = len(items)
    sujet = ("Codeur : %s" % items[0]["title"][:60]) if n == 1 else "Codeur : %d projets pour toi" % n
    corps = "".join(_bloc(i, brouillons[i["id"]]) for i in items)
    html_body = """<div style="max-width:680px;margin:0 auto;padding:26px 18px;background:#fff">
  <div style="font:700 15px -apple-system,Segoe UI,sans-serif;color:#0f172a;margin:0 0 4px">Veille Codeur</div>
  <div style="font:400 13px -apple-system,Segoe UI,sans-serif;color:#6b7280;margin:0 0 22px">
    {n} projet(s) au dessus du seuil. Le premier arrivé avec une vraie réponse gagne.</div>
  {corps}
  <div style="font:400 12px -apple-system,Segoe UI,sans-serif;color:#9ca3af;border-top:1px solid #eceff3;padding-top:14px">
    Envoyé par tools/codeur-watch. Les brouillons sont générés à partir du brief, relis avant d'envoyer.</div>
</div>""".format(n=n, corps=corps)
    return envoyer_html(sujet, html_body)
