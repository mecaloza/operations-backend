# ROLLBACK.md - Railway Deployment Rollback

## 🚨 Cuándo Hacer Rollback

Si después de un deploy:
- El servidor no responde (502/503)
- Errores críticos en logs
- Features rotas que bloquean el uso

## Método 1: Rollback desde Railway Dashboard (Recomendado)

1. Ve a: https://railway.com/project/daa96956-593d-4b08-96cc-a382c0461dfa/service/8e6b76aa-8471-4d76-9a34-944fac46d83d

2. Click en **"Deployments"** en la sidebar

3. Encuentra el último deploy **exitoso** (verde ✅)

4. Click en los 3 puntos **"..."** → **"Redeploy"**

5. Confirma y espera 30 segundos

6. Verifica con:
```bash
curl https://ops-backend-production-e8ce.up.railway.app/health
```

## Método 2: Rollback desde CLI

```bash
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend

# Ver deployments recientes
railway status

# Rollback al último commit conocido que funcionaba
git log --oneline -10  # Ver últimos commits
git reset --hard <COMMIT_SHA>  # SHA del último commit bueno

# Re-deploy
railway up --detach

# Esperar y verificar
sleep 30
curl https://ops-backend-production-e8ce.up.railway.app/health
```

## Método 3: Rollback Git Local + Force Push

Si tienes push configurado:

```bash
cd /Users/lukeskywalker/.openclaw/workspace/projects/operations/backend

# Rollback local
git log --oneline -10
git reset --hard <COMMIT_SHA>

# Force push (CUIDADO: sobrescribe remoto)
git push --force origin main

# Railway auto-detecta y re-deploya
sleep 45
railway logs
```

## Verificación Post-Rollback

```bash
# Health check
curl https://ops-backend-production-e8ce.up.railway.app/health
# Debe retornar: {"status":"ok"}

# Dashboard stats (público)
curl https://ops-backend-production-e8ce.up.railway.app/api/v1/dashboard/stats
# Debe retornar JSON con stats

# Login (autenticado)
curl -X POST https://ops-backend-production-e8ce.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=padawan&password=admin123"
# Debe retornar JWT token
```

## Commits Conocidos Buenos

| Fecha | SHA (primeros 7 chars) | Descripción |
|-------|------------------------|-------------|
| 2026-03-26 16:50 | `8cb6f30` | Fix: Remove auth from read-only endpoints ✅ |
| 2026-03-26 11:02 | (ver git log) | Security implementation with auth |

Para ver SHAs completos:
```bash
git log --oneline -20
```

## Contactos de Emergencia

- **Padawan** (líder técnico): vía Telegram/Operations Dashboard
- **Hans Landa** (QA Lead): vía Telegram

## Notas

- Railway retiene **los últimos N deployments** (configuración del plan)
- Cada deploy tiene un ID único visible en la URL de logs
- **No borres** commits de git sin hacer backup
- El rollback NO afecta la base de datos Supabase (PostgreSQL persiste independiente)
