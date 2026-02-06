# Teste Técnico - Desenvolvedor Pleno RPA

## Contexto

Você foi contratado para desenvolver um sistema de coleta de dados que extrai informações de uma fonte web e as disponibiliza via API REST.

## Objetivo

Construir uma aplicação que:

1. Colete dados do site Oscar Winning Films
2. Exponha os resultados via API REST
3. Persista os dados coletados em arquivos estruturados (JSON)
4. Utilize paralelismo para otimizar a coleta

---

## Site Alvo

### Oscar Winning Films

**URL:** https://www.scrapethissite.com/pages/ajax-javascript/

**Características:** Página dinâmica que carrega dados via JavaScript

**Dados a coletar:**
- Title
- Nominations
- Awards
- Best Picture (boolean)

---

## Requisitos Técnicos

### Obrigatórios

| Requisito | Descrição |
|-----------|-----------|
| **Selenium** | Deve estar disponível para automação quando necessário |
| **asyncio** | Implementar paralelismo com asyncio para otimizar a coleta |
| **Pydantic** | Validar e tipar todos os dados coletados com Pydantic models |
| **FastAPI** | Expor endpoints REST para trigger e consulta |
| **Persistência** | Salvar resultados em arquivos JSON no volume `./data` |

### Endpoints da API

```
POST /crawl/oscar      → Executa coleta do Oscar Films
GET  /results/{job_id} → Retorna resultados de um job
```

---

## Critérios de Avaliação

| Critério | Peso |
|----------|------|
| **Análise e estratégia** | Alto - Escolha inteligente da abordagem de coleta |
| **Qualidade do código** | Alto - Organização, legibilidade, boas práticas |
| **Funcionamento** | Alto - A solução deve funcionar corretamente |
| **Uso adequado das ferramentas** | Médio - Selenium, asyncio, Pydantic, FastAPI |
| **Tratamento de erros** | Médio - Robustez e resiliência |
| **Documentação** | Baixo |

---

## Ambiente de Desenvolvimento

### Nix + direnv (Obrigatório - Linux)

#### 1. Instalar Nix

```bash
sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install) --daemon
```

#### 2. Habilitar Flakes

Adicione ao `~/.config/nix/nix.conf`:

```
experimental-features = nix-command flakes
```

#### 3. Instalar direnv

Use o gerenciador de pacotes da sua distro:

```bash
# Debian/Ubuntu
sudo apt install direnv

# Fedora
sudo dnf install direnv

# Arch
sudo pacman -S direnv
```

Adicione ao seu shell (`~/.bashrc` ou `~/.zshrc`):

```bash
eval "$(direnv hook bash)"  # ou zsh
```

#### 4. Rodar

O `.envrc` e `flake.nix` já vêm prontos no repositório. Basta permitir o direnv e o ambiente será carregado automaticamente:

```bash
direnv allow
```

Commite o `flake.lock` no seu repositório.

---

## Regras

1. **Entrega:** Fork deste repositório
2. **Dúvidas:** Envie por email - ti@bpcreditos.com.br | gabrielpelizzaro@gmail.com ou entre em contato no whatsapp do Gabriel

---

**Queremos ver como você pensa, não apenas como você escreve código.**

---

## Solução

### Arquitetura

Dois serviços independentes orquestrados via Docker Compose:

- **crawler-api** — Gateway REST (FastAPI). Recebe requisições, gera `job_id`, delega a coleta ao serviço oscar e serve os resultados lendo os JSONs do volume compartilhado.
- **crawler-oscar** — Worker de scraping (FastAPI + httpx + Selenium). Executa a coleta em background e persiste o resultado em `./data/{job_id}.json`.

A comunicação entre os serviços é via HTTP. A persistência é feita através de um volume compartilhado (`./data`), evitando a necessidade de um banco de dados.

### Estratégia de Coleta

Ao analisar o site alvo, identifiquei que a página carrega os dados via requisições AJAX para o mesmo endpoint com os parâmetros `?ajax=true&year={ano}`, retornando JSON puro. Isso permitiu uma abordagem em duas camadas:

1. **Primária — HTTP direto (httpx):** Requisições async diretamente ao endpoint AJAX. Mais rápido, leve e sem overhead de browser.
2. **Fallback — Selenium:** Caso o HTTP falhe após 3 tentativas com backoff exponencial, o Selenium assume como fallback, garantindo resiliência.

### Paralelismo

- `asyncio.gather()` dispara a coleta de todos os anos simultaneamente.
- O fallback Selenium (síncrono) é executado via `asyncio.to_thread()` para não bloquear o event loop.
- A API retorna imediatamente com o `job_id` enquanto a coleta roda em `BackgroundTasks`.

### Tratamento de Erros

- **Retry com backoff exponencial** (3 tentativas) nas requisições HTTP.
- **Fallback HTTP → Selenium** por ano, isolando falhas.
- **Falha parcial:** Se alguns anos falham mas outros succedem, o status é `completed` com mensagem de erro parcial.
- **Falha total:** Se todos os anos falham, o status é `failed`.
- **Validação de path traversal** no endpoint `GET /results/{job_id}`.
- **502** quando o serviço oscar está indisponível.

### Como Executar

```bash
# Docker (recomendado)
docker-compose up --build
# API disponível em http://localhost:8000

# Desenvolvimento local (requer Nix + direnv)
direnv allow
cd app/crawler-oscar && uv sync && uv run pytest
cd app/crawler-api && uv sync && uv run pytest
```

### Testes

31 testes cobrindo modelos, endpoints, lógica de scraping, retries, fallback e cenários de falha:

```bash
cd app/crawler-oscar && uv run pytest -v   # 20 testes
cd app/crawler-api && uv run pytest -v     # 11 testes
```
