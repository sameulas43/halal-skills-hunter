"""
🔍 SENTINEL — SKILLS HUNTER AGENT
Cherche des ressources sur GitHub, Reddit, StackOverflow.
- Scan sécurité ligne par ligne /100
- Analyse pertinence via Groq LLM
- Signale au Manager uniquement les ressources validées
- Bloque tout ce qui est dangereux
"""

import os, re, json, time, requests, schedule, threading
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify
from groq import Groq

import sys
sys.path.append(os.path.dirname(__file__))
try:
    from sentinel_config import *
except:
    pass

# Lecture directe des variables — fallback si config non chargé
DISCORD_WEBHOOK = os.getenv("DW_URL", os.getenv("DISCORD_WEBHOOK_URL", ""))
GROQ_API_KEY    = os.getenv("LA", os.getenv("GROQ_API_KEY", ""))
AGENT_SECRET    = os.getenv("SS", os.getenv("SENTINEL_SECRET", "sentinel-secret-key"))
MANAGER_URL     = os.getenv("MANAGER_URL", "http://localhost:5001")

# ─── INIT ─────────────────────────────────────────────────
app   = Flask(__name__)
groq  = Groq(api_key=GROQ_API_KEY)

GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN", "")
MAIL_ADDRESS = os.getenv("MF", "")      # ton@gmail.com
MAIL_PASSWORD = os.getenv("MP", "") # App Password Gmail

SEARCH_TOPICS = [
    "ib_insync interactive brokers python",
    "DCA investing bot python",
    "portfolio rebalancing python ETF",
    "discord trading bot python",
    "algorithmic trading python yfinance",
    "backtesting strategy python",
    "ethical investing screener python",
]

# ─── HELPERS ──────────────────────────────────────────────
def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def send_discord(title: str, fields: list, color: int = 0xC9A84C):
    embed = {
        "title": title, "color": color, "fields": fields,
        "footer": {"text": f"🔍 SENTINEL Skills Hunter • {now_str()}"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    try:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
    except Exception as e:
        print(f"❌ Discord : {e}")

def send_email(subject: str, body_html: str, attachment_path: str = None):
    """Envoie un email Gmail avec pièce jointe optionnelle"""
    if not MAIL_ADDRESS or not MAIL_PASSWORD:
        print("⚠️ Email non configuré — MAIL_ADDRESS ou GMAIL_APP_PASSWORD manquant")
        return False

    try:
        msg = MIMEMultipart("mixed")
        msg["From"]    = f"SENTINEL Skills Hunter <{MAIL_ADDRESS}>"
        msg["To"]      = MAIL_ADDRESS
        msg["Subject"] = subject

        # Corps HTML
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        # Pièce jointe .md si fournie
        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = Path(attachment_path).name
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)

        # Envoi via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(MAIL_ADDRESS, MAIL_PASSWORD)
            smtp.send_message(msg)

        print(f"✅ Email envoyé → {MAIL_ADDRESS}")
        return True

    except Exception as e:
        print(f"❌ Email erreur : {e}")
        return False

def build_email_html(skills: list, date: str) -> str:
    """Génère le HTML de l'email hebdomadaire"""
    rows = ""
    for s in skills[:10]:
        sec    = s.get("security", {})
        score  = sec.get("score", 0)
        color  = "#2ECC71" if score >= 80 else "#F39C12" if score >= 60 else "#E74C3C"
        rel    = s.get("relevance", {}).get("reason", "")[:80]
        rows  += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #2a2a2a;">
                <a href="{s['url']}" style="color:#C9A84C;text-decoration:none;">
                    <strong>{s['title'][:50]}</strong>
                </a><br>
                <small style="color:#aaa;">{s.get('source','')}</small>
            </td>
            <td style="padding:8px;border-bottom:1px solid #2a2a2a;color:#ccc;">
                {s.get('description','')[:80]}
            </td>
            <td style="padding:8px;border-bottom:1px solid #2a2a2a;text-align:center;">
                <span style="background:{color};color:#000;padding:2px 8px;
                             border-radius:10px;font-weight:bold;">
                    {score}/100
                </span>
            </td>
            <td style="padding:8px;border-bottom:1px solid #2a2a2a;color:#aaa;font-size:12px;">
                {rel}
            </td>
        </tr>"""

    return f"""
    <html><body style="background:#0F1114;color:#E8E4DC;font-family:Arial,sans-serif;margin:0;padding:20px;">
        <div style="max-width:800px;margin:0 auto;">

            <!-- Header -->
            <div style="background:#161A1F;border:1px solid rgba(201,168,76,0.3);
                        border-radius:12px;padding:24px;text-align:center;margin-bottom:20px;">
                <h1 style="color:#C9A84C;margin:0;font-size:28px;letter-spacing:4px;">
                    🛡️ SENTINEL
                </h1>
                <p style="color:#888;margin:8px 0 0;">Skills Hunter — Rapport du {date}</p>
            </div>

            <!-- Stats -->
            <div style="display:flex;gap:12px;margin-bottom:20px;">
                <div style="flex:1;background:#161A1F;border-radius:8px;padding:16px;text-align:center;">
                    <div style="font-size:28px;color:#2ECC71;font-weight:bold;">{len(skills)}</div>
                    <div style="color:#888;font-size:12px;">Skills validés</div>
                </div>
                <div style="flex:1;background:#161A1F;border-radius:8px;padding:16px;text-align:center;">
                    <div style="font-size:28px;color:#C9A84C;font-weight:bold;">
                        {len([s for s in skills if s.get('security',{}).get('score',0)>=80])}
                    </div>
                    <div style="color:#888;font-size:12px;">Score ≥ 80/100</div>
                </div>
                <div style="flex:1;background:#161A1F;border-radius:8px;padding:16px;text-align:center;">
                    <div style="font-size:28px;color:#3B82F6;font-weight:bold;">
                        {len([s for s in skills if 'GitHub' in s.get('source','')])}
                    </div>
                    <div style="color:#888;font-size:12px;">Sources GitHub</div>
                </div>
            </div>

            <!-- Tableau skills -->
            <div style="background:#161A1F;border-radius:8px;overflow:hidden;margin-bottom:20px;">
                <div style="padding:16px;border-bottom:1px solid rgba(201,168,76,0.2);">
                    <h2 style="color:#C9A84C;margin:0;font-size:16px;">🔍 Meilleures ressources</h2>
                </div>
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:#0F1114;">
                            <th style="padding:10px 8px;text-align:left;color:#888;font-size:12px;">Ressource</th>
                            <th style="padding:10px 8px;text-align:left;color:#888;font-size:12px;">Description</th>
                            <th style="padding:10px 8px;text-align:center;color:#888;font-size:12px;">Sécurité</th>
                            <th style="padding:10px 8px;text-align:left;color:#888;font-size:12px;">Pertinence IA</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>

            <!-- Footer -->
            <div style="text-align:center;color:#555;font-size:12px;padding:16px;">
                🛡️ SENTINEL — Rapport automatique | Skills Hunter<br>
                Le fichier complet est joint à cet email (.md)
            </div>
        </div>
    </body></html>
    """

def report_to_manager(message: str, details: dict = None):
    """Envoie un rapport au Manager Agent"""
    try:
        requests.post(f"{MANAGER_URL}/report",
                      json={"agent": "skills_hunter", "message": message, "details": details or {}},
                      headers={"X-Secret": AGENT_SECRET}, timeout=10)
    except:
        pass  # Manager peut être offline, on continue

def signal_skill_to_manager(title: str, desc: str, url: str, score: int):
    """Signale un skill validé au Manager pour décision"""
    try:
        requests.post(f"{MANAGER_URL}/skill_found",
                      json={"title": title, "description": desc,
                            "url": url, "security_score": score},
                      headers={"X-Secret": AGENT_SECRET}, timeout=10)
        print(f"📡 Skill → Manager : {title}")
    except:
        print("❌ Manager injoignable — skill sauvegardé localement")

# ─── GROQ — ANALYSE ───────────────────────────────────────
def ask_groq(prompt: str) -> str:
    try:
        r = groq.chat.completions.create(
            model=GROQ_MODEL_FAST,
            messages=[
                {"role": "system",
                 "content": "Tu es l'agent Skills Hunter de SENTINEL. "
                             "Tu analyses des ressources techniques pour un bot de DCA éthique. "
                             "Tes réponses sont courtes, précises, en français."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200, temperature=0.2
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Analyse indisponible: {e}"

def groq_security_analysis(title: str, content: str) -> dict:
    """Groq analyse la dangerosité d'un code"""
    snippet = content[:500] if content else "Pas de contenu disponible"
    verdict = ask_groq(
        f"Analyse ce code/ressource : '{title}'. Extrait : {snippet}\n"
        f"Est-ce dangereux pour un bot de trading ? Réponds: SAFE ou DANGER et pourquoi en 1 phrase."
    )
    is_safe = "SAFE" in verdict.upper() and "DANGER" not in verdict.upper()
    return {"groq_verdict": verdict, "groq_safe": is_safe}

def groq_relevance(title: str, desc: str) -> dict:
    """Groq évalue la pertinence pour SENTINEL"""
    verdict = ask_groq(
        f"Ressource : '{title}' — {desc[:200]}\n"
        f"Est-ce utile pour AU MOINS UN de ces sujets : "
        f"trading automatisé, ETF, portfolio, DCA, backtesting, "
        f"Interactive Brokers, yfinance, Discord bot, Python finance, "
        f"énergie propre, agriculture, métaux, investissement algorithmique ? "
        f"Si oui → PERTINENT. Si complètement hors sujet → NON-PERTINENT. "
        f"Une raison courte. Sois large dans ton jugement."
    )
    relevant = "NON-PERTINENT" not in verdict.upper()
    return {"relevant": relevant, "reason": verdict}

# ─── SCAN SÉCURITÉ ────────────────────────────────────────
def security_scan(url: str, content: str = "") -> dict:
    """
    Analyse sécurité complète /100
    Bloque si score < SECURITY_MIN_SCORE (80)
    """
    score  = 100
    issues = []

    # Domaine blacklisté
    for domain in BLACKLISTED_DOMAINS:
        if domain in url:
            return {"score": 0, "safe": False,
                    "verdict": f"🚫 Domaine blacklisté : {domain}", "issues": []}

    # HTTPS obligatoire
    if not url.startswith("https://"):
        score -= 20
        issues.append("⚠️ Pas HTTPS")

    # Patterns dangereux ligne par ligne
    if content:
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern in DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    score -= 25
                    issues.append(f"🚨 Ligne {i} : pattern dangereux ({pattern[:25]})")
                    if score <= 0:
                        break
            if score <= 0:
                break

    # GitHub = source fiable
    if "github.com" in url:
        score = min(100, score + 5)

    # Reddit avec bonne réputation
    if "reddit.com" in url:
        score = min(100, score + 3)

    # Analyse Groq si le score est limite
    groq_result = {}
    if 40 <= score <= 80 and content:
        groq_result = groq_security_analysis(url.split("/")[-1], content)
        if not groq_result.get("groq_safe"):
            score -= 15
            issues.append(f"🤖 Groq: {groq_result.get('groq_verdict', '')[:50]}")

    safe    = score >= SECURITY_MIN_SCORE
    verdict = ("✅ Sécurisé" if score >= 80
               else "🟡 Limite" if score >= 50
               else "🔴 Dangereux")

    return {
        "score": max(0, score), "safe": safe,
        "verdict": verdict, "issues": issues,
        "groq": groq_result
    }

# ─── SOURCES ──────────────────────────────────────────────
def fetch_github_readme(repo_full_name: str) -> str:
    """Récupère le README d'un repo pour analyse"""
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        r = requests.get(
            f"https://api.github.com/repos/{repo_full_name}/readme",
            headers=headers, timeout=8
        )
        if r.status_code == 200:
            import base64
            return base64.b64decode(r.json().get("content", "")).decode("utf-8", errors="ignore")[:1000]
    except:
        pass
    return ""

def search_github(topic: str, max_results: int = 5) -> list:
    results = []
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        r = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": topic, "sort": "stars", "order": "desc", "per_page": max_results},
            headers=headers, timeout=10
        )
        if r.status_code == 200:
            for repo in r.json().get("items", []):
                # Récupère le README pour analyse
                readme = fetch_github_readme(repo["full_name"])
                scan   = security_scan(repo["html_url"], readme)

                if not scan["safe"]:
                    print(f"⛔ Bloqué : {repo['full_name']} (score {scan['score']})")
                    continue

                # Analyse pertinence
                desc       = repo.get("description") or ""
                relevance  = groq_relevance(repo["full_name"], desc)

                if not relevance["relevant"]:
                    print(f"⏭️ Non pertinent : {repo['full_name']}")
                    continue

                results.append({
                    "title":       repo["full_name"],
                    "url":         repo["html_url"],
                    "description": desc[:200],
                    "stars":       repo.get("stargazers_count", 0),
                    "language":    repo.get("language", ""),
                    "source":      "GitHub",
                    "security":    scan,
                    "relevance":   relevance,
                })
                time.sleep(0.5)
    except Exception as e:
        print(f"❌ GitHub : {e}")

    return results

def search_reddit(subreddit: str, query: str, max_results: int = 5) -> list:
    results = []
    headers = {"User-Agent": "SENTINEL-SkillsHunter/1.0"}

    try:
        r = requests.get(
            f"https://www.reddit.com/r/{subreddit}/search.json",
            params={"q": query, "sort": "relevance", "limit": max_results, "restrict_sr": 1},
            headers=headers, timeout=10
        )
        if r.status_code == 200:
            for post in r.json().get("data", {}).get("children", []):
                d   = post["data"]
                if d.get("score", 0) < 10:
                    continue
                url  = f"https://reddit.com{d.get('permalink', '')}"
                text = d.get("selftext", "")
                scan = security_scan(url, text)

                if not scan["safe"]:
                    continue

                relevance = groq_relevance(d.get("title", ""), text[:200])
                if not relevance["relevant"]:
                    continue

                results.append({
                    "title":       d.get("title", "")[:100],
                    "url":         url,
                    "description": text[:200],
                    "score":       d.get("score", 0),
                    "source":      f"Reddit r/{subreddit}",
                    "security":    scan,
                    "relevance":   relevance,
                })
    except Exception as e:
        print(f"❌ Reddit : {e}")

    return results

def search_stackoverflow(query: str, max_results: int = 5) -> list:
    results = []

    try:
        r = requests.get(
            "https://api.stackexchange.com/2.3/search/advanced",
            params={"order": "desc", "sort": "votes", "q": query,
                    "site": "stackoverflow", "pagesize": max_results, "accepted": "True"},
            timeout=10
        )
        if r.status_code == 200:
            for item in r.json().get("items", []):
                if item.get("score", 0) < 5:
                    continue
                url  = item.get("link", "")
                scan = security_scan(url)

                if not scan["safe"]:
                    continue

                title = item.get("title", "")
                desc  = f"Score: {item.get('score')} | Réponses: {item.get('answer_count')}"
                relevance = groq_relevance(title, desc)

                if not relevance["relevant"]:
                    continue

                results.append({
                    "title":       title[:100],
                    "url":         url,
                    "description": desc,
                    "source":      "StackOverflow",
                    "security":    scan,
                    "relevance":   relevance,
                })
    except Exception as e:
        print(f"❌ StackOverflow : {e}")

    return results

# ─── RECHERCHE COMPLÈTE ───────────────────────────────────
def run_search(topics: list = None):
    """Lance la recherche complète"""
    print(f"\n{'='*50}")
    print(f"🔍 Skills Hunter — {now_str()}")
    print(f"{'='*50}\n")

    if not topics:
        topics = SEARCH_TOPICS

    all_skills = []
    date = datetime.now().strftime("%Y-%m-%d")

    # GitHub
    print("📦 GitHub...")
    for topic in topics[:3]:
        results = search_github(topic, 3)
        all_skills.extend(results)
        time.sleep(2)

    # Reddit
    print("💬 Reddit...")
    all_skills.extend(search_reddit("algotrading",    "python DCA bot", 5))
    time.sleep(2)
    all_skills.extend(search_reddit("investing",      "ETF automation python", 3))
    time.sleep(2)

    # StackOverflow
    print("📚 StackOverflow...")
    all_skills.extend(search_stackoverflow("interactive brokers python ib_insync", 5))

    # Dédoublonnage
    seen  = set()
    uniq  = []
    for s in all_skills:
        if s["url"] not in seen:
            seen.add(s["url"])
            uniq.append(s)

    print(f"\n✅ {len(uniq)} skills validés trouvés")

    # Rapport Discord
    send_discord(
        f"🔍 Skills Hunter — {len(uniq)} ressources validées",
        [
            {"name": "📊 Total validé", "value": f"**{len(uniq)}** ressources sécurisées + pertinentes", "inline": False},
            {"name": "🔒 Sécurité",    "value": f"Score minimum requis : **{SECURITY_MIN_SCORE}/100**", "inline": True},
            {"name": "🧠 Filtre IA",   "value": "Groq a vérifié la pertinence", "inline": True},
        ],
        color=0x2ECC71
    )

    # Signale les meilleurs au Manager
    top_skills = sorted(uniq, key=lambda x: x["security"]["score"], reverse=True)[:5]
    for skill in top_skills:
        signal_skill_to_manager(
            title=skill["title"],
            desc=skill["description"],
            url=skill["url"],
            score=skill["security"]["score"]
        )
        time.sleep(1)

    # 📧 Email hebdomadaire avec rapport complet
    summary_path = f"skills-output/WEEKLY-SUMMARY-{date}.md"
    os.makedirs("skills-output", exist_ok=True)

    # Génère le fichier .md résumé
    summary_path = f"skills-output/WEEKLY-SUMMARY-{date}.md"
    os.makedirs("skills-output", exist_ok=True)

    md_lines = [
        f"# 🛡️ SENTINEL — Weekly Skills Report — {date}",
        f"_{len(uniq)} ressources sécurisées et pertinentes_\n",
        "---\n"
    ]
    for i, s in enumerate(uniq[:10], 1):
        md_lines += [
            f"## {i}. {s['title']}",
            f"- 🔗 {s['url']}",
            f"- 📝 {s.get('description','')[:150]}",
            f"- 🌐 {s.get('source','')}",
            f"- 🔒 Sécurité : {s['security']['verdict']} ({s['security']['score']}/100)",
            f"- 🧠 Pertinence : {s.get('relevance',{}).get('reason','')[:100]}\n"
        ]
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # 📊 Rapport complet sur Discord (au lieu de l'email)
    # Envoie les top 5 skills détaillés
    top5 = sorted(uniq, key=lambda x: x["security"]["score"], reverse=True)[:5]
    skills_text = "\n".join(
        f"**{i}.** [{s['title']}]({s['url']})\n"
        f"   🔒 {s['security']['score']}/100 | 🌐 {s.get('source','')}"
        for i, s in enumerate(top5, 1)
    )

    send_discord(
        f"📋 WEEKLY SKILLS REPORT — {date}",
        [
            {"name": "📊 Total validé",
             "value": f"**{len(uniq)}** ressources sécurisées + pertinentes",
             "inline": True},
            {"name": "🔒 Score min",
             "value": f"**{SECURITY_MIN_SCORE}/100**",
             "inline": True},
            {"name": "─────────────────", "value": " ", "inline": False},
            {"name": "🏆 Top 5 ressources",
             "value": skills_text or "Aucune",
             "inline": False},
            {"name": "─────────────────", "value": " ", "inline": False},
            {"name": "🧠 Pour améliorer Claude",
             "value": "Uploader `WEEKLY-SUMMARY.md` dans le projet Claude chaque lundi",
             "inline": False},
        ],
        color=0x2ECC71
    )

    # Rapport au Manager
    report_to_manager(
        f"{len(uniq)} skills trouvés et validés",
        {"count": len(uniq), "top": [s["title"] for s in top_skills]}
    )

    return uniq

# ─── API FLASK ────────────────────────────────────────────
def check_secret():
    return request.headers.get("X-Secret") == AGENT_SECRET

@app.route("/health")
def health():
    return jsonify({"status": "online", "agent": "skills_hunter", "time": now_str()})

@app.route("/task", methods=["POST"])
def receive_task():
    """Reçoit une tâche du Manager"""
    if not check_secret():
        return jsonify({"error": "Unauthorized"}), 401

    data  = request.json
    task  = data.get("task", "")
    topic = data.get("topic", "")

    print(f"📨 Tâche reçue du Manager : {task} — {topic}")

    if task == "weekly_search":
        threading.Thread(target=run_search, daemon=True).start()
        return jsonify({"status": "started"})

    if task == "search_topic" and topic:
        threading.Thread(
            target=run_search, args=([topic],), daemon=True
        ).start()
        return jsonify({"status": "started", "topic": topic})

    return jsonify({"status": "unknown_task"})

# ─── PLANIFICATION ────────────────────────────────────────
def setup_schedule():
    schedule.every().monday.at("08:00").do(run_search)
    print("⏰ Recherche planifiée : lundi 08:00")

# ─── MAIN ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print(f"🔍 SENTINEL — SKILLS HUNTER v{VERSION}")
    print(f"🕐 Démarré le {now_str()}")
    print(f"🧠 LLM : Groq {GROQ_MODEL_FAST}")
    print("=" * 55)

    send_discord("🚀 SENTINEL Skills Hunter — Opérationnel", [
        {"name": "✅ Status",    "value": "Online H24 sur Railway",           "inline": True},
        {"name": "🧠 LLM",      "value": f"Groq {GROQ_MODEL_FAST}",          "inline": True},
        {"name": "🔍 Sources",  "value": "GitHub + Reddit + StackOverflow",   "inline": False},
        {"name": "🔒 Sécurité", "value": f"Score min : {SECURITY_MIN_SCORE}/100 | Scan ligne par ligne", "inline": False},
        {"name": "📅 Planning", "value": "Recherche chaque lundi à 08:00",    "inline": False},
    ], color=0x2ECC71)

    setup_schedule()

    # API Flask dans un thread séparé
    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5002, debug=False),
        daemon=True
    )
    flask_thread.start()
    print("🌐 API Skills Hunter démarrée sur port 5002")

    # Première recherche immédiate
    run_search()

    while True:
        schedule.run_pending()
        time.sleep(60)
