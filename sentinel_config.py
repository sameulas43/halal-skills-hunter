"""
⚙️ SENTINEL — Configuration partagée
Utilisé par les 3 agents : Manager, Skills, Trading
"""

import os

# ─── IDENTITÉ ─────────────────────────────────────────────
PROJECT_NAME    = "SENTINEL"
VERSION         = "1.0.0"

# ─── DISCORD ──────────────────────────────────────────────
DISCORD_WEBHOOK         = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_TOKEN           = os.getenv("DISCORD_TOKEN", "")
DISCORD_CHANNEL_ID      = os.getenv("DISCORD_CHANNEL_ID", "")

# ─── LLM — GROQ (gratuit) ─────────────────────────────────
GROQ_API_KEY            = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL              = "llama3-70b-8192"       # Meilleur modèle Groq gratuit
GROQ_MODEL_FAST         = "llama3-8b-8192"        # Rapide pour tâches simples

# ─── INTER-AGENTS (HTTP) ──────────────────────────────────
MANAGER_URL             = os.getenv("MANAGER_URL", "http://localhost:5001")
SKILLS_URL              = os.getenv("SKILLS_URL",  "http://localhost:5002")
TRADING_URL             = os.getenv("TRADING_URL", "http://localhost:5003")
AGENT_SECRET            = os.getenv("AGENT_SECRET", "sentinel-secret-key")

# ─── INTERACTIVE BROKERS ──────────────────────────────────
IB_HOST                 = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT                 = int(os.getenv("IB_PORT", "7496"))   # 7496=live / 7497=paper
IB_CLIENT_ID            = int(os.getenv("IB_CLIENT_ID", "1"))

# ─── PORTEFEUILLE CIBLE ───────────────────────────────────
PORTFOLIO = {
    "SGOL": 0.15,   # Or physique
    "PHAG": 0.10,   # Argent physique
    "ICLN": 0.15,   # Clean Energy ETF
    "ENPH": 0.10,   # Enphase Energy
    "MOO":  0.10,   # Agro ETF
    "DBA":  0.10,   # Agriculture ETF
    "SPUS": 0.15,   # Shariah ETF
    "HLAL": 0.10,   # Shariah ETF
    "PHO":  0.05,   # Water ETF
}

# ─── RÈGLES RISQUE ────────────────────────────────────────
DCA_AMOUNT              = 50.0      # € par mois
DIP_THRESHOLD           = -0.05     # -5% → signal achat
MAX_POSITION_PCT        = 0.05      # Max 5% capital par ordre
DRAWDOWN_MAX            = 0.15      # -15% → alerte urgente
MIN_CASH                = 10.0      # € minimum avant achat
REBALANCE_THRESHOLD     = 0.05      # 5% d'écart → rebalancement

# ─── SÉCURITÉ SKILLS ──────────────────────────────────────
SECURITY_MIN_SCORE      = 80        # Score minimum /100 pour accepter
PAPER_TRADING_DAYS      = 14        # Jours de test avant live

# ─── ACTIFS VALIDÉS ───────────────────────────────────────
VALIDATED_ASSETS = [
    "SGOL", "PHAG", "SLV", "PPLT", "PALL",
    "ICLN", "FSLR", "NEE", "RUN", "ENPH", "TAN", "FAN",
    "MOO", "DBA", "ADM", "BG", "CTVA",
    "WOOD", "WY", "PHO", "FIW", "XYL",
    "SPUS", "HLAL",
]

# ─── BLACKLIST DOMAINES ───────────────────────────────────
BLACKLISTED_DOMAINS = [
    "pastebin.com", "grabify.link", "iplogger.org",
    "zerobin.net", "bit.ly", "tinyurl.com",
]

# ─── PATTERNS DANGEREUX ───────────────────────────────────
DANGEROUS_PATTERNS = [
    r"eval\s*\(", r"exec\s*\(", r"__import__",
    r"subprocess\.call", r"os\.system",
    r"keylogger", r"backdoor", r"reverse.?shell",
    r"crypto.?miner", r"steal.?token",
    r"delete.?files", r"rm\s+-rf",
    r"os\.environ\[.*(PASSWORD|TOKEN|SECRET|KEY)",
    r"requests\.post.*(?:discord|telegram).*token",
]
