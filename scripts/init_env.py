"""Create local secrets once; never print secrets or overwrite existing settings."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    print(".env already exists; left unchanged.")
else:
    content = (root / ".env.example").read_text(encoding="utf-8")
    content = content.replace("JWT_SECRET=\n", f"JWT_SECRET={secrets.token_urlsafe(48)}\n")
    content = content.replace("POSTGRES_PASSWORD=\n", f"POSTGRES_PASSWORD={secrets.token_hex(24)}\n")
    target.write_text(content, encoding="utf-8")
    print("Created .env with random local secrets (gitignored).")
