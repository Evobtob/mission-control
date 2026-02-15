# NIA OS — Mission Control

Sistema de controlo operacional para OpenClaw com versionamento robusto.

---

## 🚀 Versões Disponíveis

| Versão | URL | Descrição | Estado |
|--------|-----|-----------|--------|
| **Latest (v2.1)** | https://evobtob.github.io/mission-control/ | Multi-page — cada secção tem página dedicada | ✅ Ativo |
| **v2.0** | https://evobtob.github.io/mission-control/v2.0/ | Multi-page base | ✅ Estável |
| **v1.2** | https://evobtob.github.io/mission-control/v1.2/ | SPA com version selector | ✅ Estável |
| **v1.1** | https://evobtob.github.io/mission-control/v1.1/ | SPA com Tasks + Cron | ✅ Estável |
| **v1.0** | https://evobtob.github.io/mission-control/v1.0/ | SPA English + Agents | ✅ Estável |

---

## ↩️ Rollback Strategy

### Se uma versão correr mal:

1. **Usar o selector no sidebar** — Troca imediata para versão anterior
2. **URL direto** — Acede diretamente a qualquer versão antiga
3. **Git checkout** — Para desenvolvimento local:
   ```bash
   git checkout v1.0  # ou v1.1, v1.2
   ```

### Estrutura de Pastas:

```
mission-control/
├── index.html          # SEMPRE a versão mais recente (v2.1+)
├── agents.html         # Página dedicada Agents (v2.x)
├── system.html         # Página dedicada System (v2.x)
├── connections.html    # Página dedicada Connections (v2.x)
├── security.html       # Página dedicada Security (v2.x)
├── tasks.html          # Página dedicada Tasks (v2.x)
├── cron.html           # Página dedicada Cron Jobs (v2.x)
├── v2.0/               # V2.0 congelada (multi-page base)
│   ├── index.html
│   ├── agents.html
│   ├── system.html
│   ├── connections.html
│   ├── security.html
│   ├── tasks.html
│   └── cron.html
├── v1.2/               # V1.2 congelada (SPA com selector)
│   └── index.html
├── v1.1/               # V1.1 congelada (SPA)
│   └── index.html
├── v1.0/               # V1.0 congelada (SPA)
│   └── index.html
├── local/              # Servidor Python local + Bridge
├── versions.json       # Manifesto de versões
└── SIMULATION_REPORT.md
```

### Tags Git:

```
v2.1 → d8715b5 (Multi-page com modals + JS)
v2.0 → 7f1224a (Multi-page base)
v1.2 → d602bfa (SPA Versioning system)
v1.1 → 9f911ab (SPA Tasks + Cron)
v1.0 → 17eea3e (SPA English + Agents)
```

### Rollback para V2.x:

```bash
# Para rollback para v2.0:
git checkout v2.0
cp v2.0/*.html .
# Commit e push

# Para rollback para SPA (v1.2):
git checkout v1.2
cp v1.2/index.html .
rm agents.html system.html connections.html security.html tasks.html cron.html
# Commit e push
```

---

## 🔄 Como Funciona

1. **Desenvolvimento** — Trabalha-se sempre no `index.html` root
2. **Commit** — `git commit -m "V1.X: nova feature"`
3. **Tag** — `git tag -a v1.X <commit>`
4. **Deploy pastas** — Copiar `index.html` para `v1.X/index.html`
5. **Push** — `git push origin main --tags`

---

## 🆘 Emergência — Rollback Rápido

### Opção 1: Selector (mais rápido)
```
Abre o Mission Control → Sidebar → Selector "Latest (v1.2)" → Escolhe v1.1 ou v1.0
```

### Opção 2: URL direto
```
https://evobtob.github.io/mission-control/v1.0/  # Vai direto para V1.0
```

### Opção 3: Reverter GitHub Pages para branch antiga
*(Se o main estiver totalmente quebrado)*
```bash
# Criar branch de hotfix a partir de tag estável
git checkout -b hotfix-v1.1 v1.1

# GitHub Settings → Pages → mudar source para hotfix-v1.1
```

---

## 📝 Manifesto de Versões

Ver `versions.json` para lista automática de versões disponíveis.

---

**Última atualização:** 2026-02-15  
**Versão atual:** v1.2  
**Responsável:** Nia 👩🏻‍💻
