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
