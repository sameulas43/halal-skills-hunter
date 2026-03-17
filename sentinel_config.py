"""
⚙️ SENTINEL — Configuration partagée
Utilisé par les 3 agents : Manager, Skills, Trading
"""

import os

# ─── IDENTITÉ ─────────────────────────────────────────────
PROJECT_NAME    = "SENTINEL"
VERSION         = "1.0.0"

# ─── DISCORD ──────────────────────────────────────────────
DISCORD_WEBHOOK         = os.getenv("DW_URL", "")
DISCORD_TOKEN           = os.getenv("BT", "")
DISCORD_CHANNEL_ID      = os.getenv("BC", "")

# ─── LLM — GROQ (gratuit) ─────────────────────────────────
GROQ_API_KEY            = os.getenv("LA", "")
GROQ_MODEL              = "llama-3.3-70b-versatile"   # Meilleur modèle Groq actuel
GROQ_MODEL_FAST         = "llama-3.1-8b-instant"       # Rapide pour tâches simples

# ─── INTER-AGENTS (HTTP) ──────────────────────────────────
MANAGER_URL             = os.getenv("MANAGER_URL", "http://localhost:5001")
SKILLS_URL              = os.getenv("SKILLS_URL",  "http://localhost:5002")
TRADING_URL             = os.getenv("TRADING_URL", "http://localhost:5003")
AGENT_SECRET            = os.getenv("SS", "sentinel-secret-key")

# ─── EMAIL ────────────────────────────────────────────────
GMAIL_ADDRESS           = os.getenv("MF", "")
GMAIL_APP_PWD           = os.getenv("MP", "")

# ─── INTERACTIVE BROKERS ──────────────────────────────────
IB_HOST                 = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT                 = int(os.getenv("IB_PORT", "7496"))
IB_CLIENT_ID            = int(os.getenv("IB_CLIENT_ID", "1"))

# ─── PORTEFEUILLE CIBLE ───────────────────────────────────
PORTFOLIO = {
    "SGOL": 0.15,
    "SLV": 0.10,
    "ICLN": 0.15,
    "ENPH": 0.10,
    "MOO":  0.10,
    "DBA":  0.10,
    "SPUS": 0.15,
    "HLAL": 0.10,
    "PHO":  0.05,
}

# ─── RÈGLES RISQUE ────────────────────────────────────────
DCA_AMOUNT              = 50.0
DIP_THRESHOLD           = -0.05
MAX_POSITION_PCT        = 0.05
DRAWDOWN_MAX            = 0.15
MIN_CASH                = 10.0
REBALANCE_THRESHOLD     = 0.05

# ─── SÉCURITÉ SKILLS ──────────────────────────────────────
SECURITY_MIN_SCORE      = 80
PAPER_TRADING_DAYS      = 14

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
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__",
    r"subprocess\.call",
    r"os\.system",
    r"keylogger",
    r"backdoor",
    r"reverse.?shell",
    r"crypto.?miner",
    r"steal.?creds",
    r"delete.?files",
    r"rm\s+-rf",
    r"exfiltrat",
]
