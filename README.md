# NIA OS — Mission Control

Sistema de controlo operacional para OpenClaw com versionamento robusto.

---

## 🚀 Versões Disponíveis

| Versão | URL | Descrição | Estado |
|--------|-----|-----------|--------|
| **Latest** | https://evobtob.github.io/mission-control/ | Sempre a versão mais recente | ✅ Ativo |
| **v1.2** | https://evobtob.github.io/mission-control/v1.2/ (n/a - é a latest) | Versioning system + selector | ✅ Ativo |
| **v1.1** | https://evobtob.github.io/mission-control/v1.1/ | Tasks + Cron Jobs tabs | ✅ Estável |
| **v1.0** | https://evobtob.github.io/mission-control/v1.0/ | English + Agent Management | ✅ Estável |

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
├── index.html          # SEMPRE a versão mais recente (v1.2+)
├── v1.0/
│   └── index.html      # V1.0 — congelada, nunca muda
├── v1.1/
│   └── index.html      # V1.1 — congelada, nunca muda
├── versions.json       # Manifesto de versões
└── SIMULATION_REPORT.md
```

### Tags Git:

```
v1.0 → 17eea3e (English + Agents)
v1.1 → 9f911ab (Tasks + Cron)
v1.2 → d602bfa (Versioning system)
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
