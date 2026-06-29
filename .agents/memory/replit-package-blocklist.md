---
name: Replit Package Blocklist & Compatibility
description: Known blocked packages and version incompatibilities in the Replit environment
---

## PostgreSQL driver
- Use `psycopg2-binary==2.9.10` for PostgreSQL connections via SQLAlchemy. Works fine on Replit.

## Blocked packages (HTTP 403 from package firewall)
- `python-jose` — blocked entirely. Use `PyJWT` instead.
  - Replace `from jose import JWTError, jwt` with `import jwt` and catch `jwt.PyJWTError`

## Version incompatibilities
- `bcrypt 5.x` breaks `passlib` — causes `ValueError: password cannot be longer than 72 bytes` during bcrypt backend initialization.
  - **Fix**: Pin `bcrypt==4.0.1` in requirements.txt (do NOT use passlib[bcrypt] which pulls latest bcrypt)

**Why:** The Replit package firewall blocks certain packages for security/licensing reasons. bcrypt 5.x introduced a breaking API change that passlib 1.7.4 doesn't handle.

**How to apply:** Whenever adding JWT or password hashing to a new Python project on Replit, use PyJWT and bcrypt==4.0.1 from the start.
