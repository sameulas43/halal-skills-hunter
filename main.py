"""
🔍 SKILLS HUNTER AGENT — Halal Ecosystem
Tourne H24 sur Railway.
Cherche chaque lundi sur GitHub + Reddit + StackOverflow
Scan sécurité /100 — Bloque si score < 50
Envoie rapport Discord + génère fichiers pour Claude
"""

import os
import json
import re
import requests
import schedule
import time
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")

SEARCH_TOPICS = [
    "ib_insync interactive brokers python",
    "halal investing python bot",
    "DCA trading bot python",
    "discord trading bot python",
    "algorithmic trading python yfinance",
    "portfolio rebalancing python",
    "backtesting python strategy",
]

# Domaines blacklistés — jamais acceptés
BLACKLISTED_DOMAINS = [
    "pastebin.com", "grabify.link", "iplogger.org",
    "zerobin.net", "privatebin.net", "hastebin.com",
    "bit.ly", "tinyurl.com", "shorturl.at"
]

# Patterns dangereux dans le code
DANGEROUS_PATTERNS = [
    r"eval\s*\(", r"exec\s*\(", r"__import__",
    r"subprocess\.call", r"os\.system",
    r"keylogger", r"backdoor", r"reverse.?shell",
    r"crypto.?miner", r"bitcoin.?miner",
    r"steal.?token", r"grab.?token",
    r"delete.?files", r"format.?disk",
    r"rm\s+-rf", r"exfiltrat",
]

def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def send_discord(title: str, fields: list, color: int = 0xC9A84C):
    embed = {
        "title": title, "color": color, "fields": fields,
        "footer": {"text": f"🔍 Skills Hunter • {now_str()}"},
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        print(f"✅ Discord → {title}")
    except Exception as e:
        print(f"❌ Discord erreur : {e}")


# ─── SCAN SÉCURITÉ ────────────────────────────────────────

def security_scan(url: str, content: str = "") -> dict:
    """
    Analyse la sécurité d'une ressource.
    Score /100 — Bloque si < 50
    """
    score = 100
    issues = []

    # Vérifie domaine blacklisté
    for domain in BLACKLISTED_DOMAINS:
        if domain in url:
            return {"score": 0, "safe": False,
                    "verdict": f"🚫 Domaine blacklisté : {domain}", "issues": []}

    # HTTPS obligatoire
    if not url.startswith("https://"):
        score -= 15
        issues.append("⚠️ Pas HTTPS")

    # Patterns dangereux dans le contenu
    if content:
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                score -= 25
                issues.append(f"🚨 Pattern dangereux : {pattern[:20]}")

    # GitHub = plus fiable
    if "github.com" in url:
        score = min(100, score + 5)

    safe = score >= 50
    verdict = "✅ Sécurisé" if score >= 80 else "🟡 À vérifier" if score >= 50 else "🔴 Dangereux"

    return {"score": score, "safe": safe, "verdict": verdict, "issues": issues}


# ─── SOURCES DE RECHERCHE ─────────────────────────────────

def search_github(topic: str, max_results: int = 5) -> list:
    """Cherche des repos GitHub sur un sujet"""
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
                scan = security_scan(repo["html_url"])
                if scan["safe"]:
                    results.append({
                        "title":       repo["full_name"],
                        "url":         repo["html_url"],
                        "description": (repo.get("description") or "")[:150],
                        "stars":       repo.get("stargazers_count", 0),
                        "language":    repo.get("language", ""),
                        "source":      "GitHub",
                        "security":    scan
                    })
    except Exception as e:
        print(f"❌ GitHub erreur : {e}")

    return results

def search_reddit(subreddit: str, query: str, max_results: int = 5) -> list:
    """Cherche des posts Reddit"""
    results = []
    headers = {"User-Agent": "HalalSkillsHunter/1.0"}

    try:
        r = requests.get(
            f"https://www.reddit.com/r/{subreddit}/search.json",
            params={"q": query, "sort": "relevance", "limit": max_results, "restrict_sr": 1},
            headers=headers, timeout=10
        )
        if r.status_code == 200:
            for post in r.json().get("data", {}).get("children", []):
                d = post["data"]
                if d.get("score", 0) < 10:
                    continue
                url = f"https://reddit.com{d.get('permalink', '')}"
                scan = security_scan(url)
                if scan["safe"]:
                    results.append({
                        "title":       d.get("title", "")[:100],
                        "url":         url,
                        "description": (d.get("selftext") or "")[:150],
                        "score":       d.get("score", 0),
                        "source":      f"Reddit r/{subreddit}",
                        "security":    scan
                    })
    except Exception as e:
        print(f"❌ Reddit erreur : {e}")

    return results

def search_stackoverflow(query: str, max_results: int = 5) -> list:
    """Cherche des questions StackOverflow"""
    results = []

    try:
        r = requests.get(
            "https://api.stackexchange.com/2.3/search/advanced",
            params={
                "order": "desc", "sort": "votes",
                "q": query, "site": "stackoverflow",
                "pagesize": max_results, "accepted": "True"
            },
            timeout=10
        )
        if r.status_code == 200:
            for item in r.json().get("items", []):
                if item.get("score", 0) < 5:
                    continue
                url = item.get("link", "")
                scan = security_scan(url)
                if scan["safe"]:
                    results.append({
                        "title":       item.get("title", "")[:100],
                        "url":         url,
                        "description": f"Score: {item.get('score')} | Réponses: {item.get('answer_count')}",
                        "score":       item.get("score", 0),
                        "source":      "StackOverflow",
                        "security":    scan
                    })
    except Exception as e:
        print(f"❌ StackOverflow erreur : {e}")

    return results


# ─── GÉNÉRATION FICHIERS MARKDOWN ─────────────────────────

def generate_skill_file(category: str, items: list, date: str) -> str:
    """Génère un fichier markdown pour une catégorie"""
    lines = [
        f"# 🔍 Skills — {category} — {date}",
        f"_Généré par Skills Hunter | {len(items)} ressources sécurisées_",
        "",
        "---",
        ""
    ]

    for i, item in enumerate(items[:5], 1):
        security = item.get("security", {})
        lines += [
            f"## {i}. {item['title']}",
            f"- 🔗 **URL** : {item['url']}",
            f"- 📝 **Description** : {item.get('description', 'N/A')}",
            f"- 🌐 **Source** : {item.get('source', 'N/A')}",
            f"- 🔒 **Sécurité** : {security.get('verdict', '?')} ({security.get('score', 0)}/100)",
            ""
        ]

    return "\n".join(lines)

def save_skills(all_results: dict, date: str):
    """Sauvegarde tous les fichiers skills"""
    os.makedirs("skills-output", exist_ok=True)
    files = []

    category_names = {
        "github_finance":   "Finance & Trading Scripts",
        "github_bots":      "Bots & Automation",
        "reddit_algo":      "Algorithmic Trading Community",
        "reddit_halal":     "Halal Finance Community",
        "stackoverflow":    "StackOverflow Solutions",
    }

    for category, items in all_results.items():
        if not items:
            continue
        name = category_names.get(category, category)
        content = generate_skill_file(name, items, date)
        filepath = f"skills-output/{category}-{date}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        files.append(filepath)
        print(f"✅ Fichier généré : {filepath}")

    # Résumé global
    total = sum(len(v) for v in all_results.values())
    summary = [
        f"# 📊 Weekly Skills Summary — {date}",
        f"_Skills Hunter — {total} ressources sécurisées cette semaine_",
        "",
        "## Catégories",
    ]
    for cat, items in all_results.items():
        summary.append(f"- **{category_names.get(cat, cat)}** : {len(items)} ressources")
    summary += ["", "---", "_Uploade ce fichier dans ton Projet Claude 🧠_"]

    with open(f"skills-output/WEEKLY-SUMMARY-{date}.md", "w") as f:
        f.write("\n".join(summary))

    return files


# ─── AGENT PRINCIPAL ──────────────────────────────────────

def run_skills_hunter():
    """Lance la recherche complète — chaque lundi"""
    print(f"\n{'='*50}")
    print(f"🔍 Skills Hunter démarré — {now_str()}")
    print(f"{'='*50}\n")

    date = datetime.now().strftime("%Y-%m-%d")
    all_results = {
        "github_finance": [],
        "github_bots":    [],
        "reddit_algo":    [],
        "reddit_halal":   [],
        "stackoverflow":  [],
    }

    # ─── GitHub ───────────────────────────────────────────
    print("📦 Recherche GitHub...")
    for topic in SEARCH_TOPICS[:3]:
        results = search_github(topic, max_results=3)
        if "bot" in topic or "discord" in topic:
            all_results["github_bots"] += results
        else:
            all_results["github_finance"] += results
        time.sleep(1)  # Rate limit

    # ─── Reddit ───────────────────────────────────────────
    print("💬 Recherche Reddit...")
    all_results["reddit_algo"]  = search_reddit("algotrading",  "python trading bot", 5)
    time.sleep(2)
    all_results["reddit_halal"] = search_reddit("IslamicFinance", "halal investing", 5)
    time.sleep(2)

    # ─── StackOverflow ────────────────────────────────────
    print("📚 Recherche StackOverflow...")
    all_results["stackoverflow"] = search_stackoverflow("interactive brokers python trading", 5)

    # ─── Stats ────────────────────────────────────────────
    total_safe    = sum(len(v) for v in all_results.values())
    total_by_cat  = {k: len(v) for k, v in all_results.items() if v}

    print(f"\n✅ Total ressources sécurisées : {total_safe}")

    # ─── Génère les fichiers ──────────────────────────────
    files = save_skills(all_results, date)

    # ─── Rapport Discord ──────────────────────────────────
    send_discord(
        f"🔍 Skills Hunter — Rapport du {date}",
        [
            {"name": "📊 Ressources trouvées",
             "value": f"**{total_safe}** ressources sécurisées cette semaine",
             "inline": False},
            {"name": "📦 GitHub Finance",
             "value": str(len(all_results["github_finance"])), "inline": True},
            {"name": "🤖 GitHub Bots",
             "value": str(len(all_results["github_bots"])),    "inline": True},
            {"name": "💬 Reddit",
             "value": str(len(all_results["reddit_algo"]) + len(all_results["reddit_halal"])),
             "inline": True},
            {"name": "📚 StackOverflow",
             "value": str(len(all_results["stackoverflow"])),  "inline": True},
            {"name": "─────────────────", "value": " ",        "inline": False},
            {"name": "📁 Action requise",
             "value": f"Uploader `WEEKLY-SUMMARY-{date}.md` dans ton Projet Claude 🧠",
             "inline": False},
        ],
        color=0x2ECC71
    )

    print(f"\n✅ Skills Hunter terminé — {now_str()}")
    return all_results


# ─── PLANIFICATION ────────────────────────────────────────

def setup_schedule():
    schedule.every().monday.at("08:00").do(run_skills_hunter)
    print("⏰ Skills Hunter planifié : chaque lundi à 08:00")

if __name__ == "__main__":
    print("=" * 50)
    print("🔍 SKILLS HUNTER AGENT — Halal Ecosystem")
    print(f"🕐 Démarré le {now_str()}")
    print("=" * 50)

    send_discord("🚀 Skills Hunter opérationnel", [
        {"name": "✅ Status",   "value": "Online sur Railway H24", "inline": True},
        {"name": "🕐 Heure",   "value": now_str(),                 "inline": True},
        {"name": "📅 Planning", "value": "Recherche chaque lundi à 08:00", "inline": False},
        {"name": "🔍 Sources",  "value": "GitHub + Reddit + StackOverflow", "inline": False},
        {"name": "🔒 Sécurité", "value": "Scan /100 — Bloque si score < 50", "inline": False},
    ], color=0x2ECC71)

    setup_schedule()

    # Lance une première recherche immédiatement
    run_skills_hunter()

    while True:
        schedule.run_pending()
        time.sleep(60)
