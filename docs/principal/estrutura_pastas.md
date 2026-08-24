# Estrutura de Diretórios (Monorepo de Microsserviços)

Este documento descreve a organização de pastas proposta para o projeto, englobando aplicações Frontend, Backends (Microsserviços), pacotes compartilhados, configurações de containers (Docker) e documentação.

A estrutura adota o padrão de **Monorepo**, facilitando o compartilhamento de código, a orquestração local com Docker Compose e a padronização das ferramentas de build/deploy.

---

## O Padrão Monorepo

O padrão **Monorepo** (*monolithic repository*) consiste em manter múltiplos projetos ou serviços em um **único repositório de controle de versão (Git)**, ao invés de gerenciar um repositório isolado para cada serviço (*Multirepo*).

No nosso ecossistema de microsserviços, frontend e Docker, esta abordagem traz vantagens indispensáveis:

### 1. Vantagens do Monorepo no Projeto
* **Compartilhamento de Código Simplificado**: Modelos de dados, tipagens (TypeScript/DTOs) e funções utilitárias são compartilhados localmente (através da pasta `packages/`) sem a necessidade de publicá-los em gerenciadores de pacotes públicos ou privados (como NPM/PyPI).
* **Orquestração Local com Docker**: Permite centralizar o arquivo `docker-compose.yml` na raiz do projeto. Com um único comando (`docker compose up`), é possível subir todo o ambiente de desenvolvimento (frontend, gateway, microsserviços e bancos de dados).
* **Commits e Alterações Atômicas**: Se uma nova feature exige mudanças no Frontend e em um Microsserviço de Backend, você pode commitar e enviar ambas as alterações de forma sincronizada na mesma branch, reduzindo problemas de incompatibilidade de versão em ambiente local.
* **Padronização de Ferramental**: Centralização de linters, regras de formatação (Prettier, ESLint, Ruff) e fluxos de CI/CD em um só lugar.

### 2. Desafios e Mitigações
* **Tamanho do Repositório**: Pode crescer rapidamente à medida que adicionamos código e builds.
  * *Mitigação*: Utilizar regras robustas no `.gitignore` e no `.dockerignore` para nunca subir pastas pesadas como `node_modules`, `.venv`, ou arquivos gerados de build local.
* **Complexidade no Pipeline de CI/CD**: Rodar build e testes para o projeto inteiro em cada alteração pode se tornar lento.
  * *Mitigação*: Configurar as ferramentas de CI/CD (GitHub Actions, GitLab CI, etc.) para utilizar filtros de caminhos (*path filtering*), disparando builds e testes apenas dos serviços específicos que sofreram modificações.

---

## Árvore de Diretórios Proposta

```text
/ (raiz do projeto)
├── apps/                           # Aplicacoes principais executaveis
│   ├── frontend/                   # Cliente Web (React + Vite)
│   │   ├── src/                    # Codigo fonte do frontend
│   │   │   ├── components/         # Componentes React (Sidebar, ProfessorProfile, DisciplinasList, StacksTable, ImageAndCarousel, MapComponent)
│   │   │   ├── App.jsx             # Orquestrador principal (Navbar, Layout, API fetch)
│   │   │   ├── main.jsx            # Ponto de entrada React + imports globais (Bootstrap, Leaflet)
│   │   │   └── custom.css          # CSS customizado para os alunos
│   │   ├── public/                 # Imagens e assets estaticos
│   │   ├── index.html              # Template base HTML
│   │   ├── vite.config.js          # Configuracoes de compilacao do Vite
│   │   └── package.json            # Dependencias do Frontend (React, Bootstrap, Leaflet)
│   │
│   ├── api-gateway/                # Ponto de entrada unico para o ecossistema (Nginx/Kong/Node)
│   │   ├── Dockerfile
│   │   └── ...
│   │
│   └── services/                   # Microsservicos do Backend
│       ├── auth-service/           # Servico de Autenticacao e Usuarios
│       │   ├── src/
│       │   ├── tests/
│       │   ├── Dockerfile
│       │   └── requirements.txt / package.json
│       │
│       ├── core-service/           # Servico com as regras de negocio principais
│       │   ├── app/                # Codigo fonte do FastAPI (main.py, api/, models/, schemas/, repositories/, services/)
│       │   ├── alembic/            # Historico de versionamento e migrations do Postgres
│       │   ├── env_example         # Modelo legivel de configuracoes de ambiente
│       │   ├── pyproject.toml      # Configuracao de dependencias do Poetry
│       │   ├── requirements.txt    # Configuracao de dependencias do pip/venv
│       │   └── ...
│       │
│       └── [outro-servico]/        # Outros microsservicos independentes
│
├── packages/                       # Pacotes/Módulos reutilizáveis compartilhados
│   ├── database-schemas/           # Modelos de dados e migrações compartilhadas
│   ├── shared-utils/               # Helpers, loggers e utilitários comuns
│   └── shared-types/               # Tipagens ou definições comuns (TS/DTOs/etc.)
│
├── docker/                         # Configurações de infraestrutura e Docker auxiliares
│   ├── dev/                        # Arquivos e scripts para ambiente de desenvolvimento
│   │   └── db-init/                # Scripts de inicialização de banco de dados
│   └── prod/                       # Configurações específicas de produção
│
├── docs/                           # Documentação técnica do projeto (manuais, diagramas)
│
├── .dockerignore                   # Lista de arquivos ignorados no contexto do Docker
├── .gitignore                      # Lista de arquivos ignorados pelo Git
├── README.md                       # Visão geral do projeto e instruções de inicialização
└── docker-compose.yml              # Orquestração local de todos os serviços (e bancos de dados)
```

---

## Descrição dos Componentes Principais

### 1. `apps/`
Nesta pasta ficam todas as aplicações independentes e que possuem seu próprio ciclo de vida/processo de execução:
- **`frontend/`**: O cliente Web. Possui seu próprio `Dockerfile` para ser empacotado de forma isolada.
- **`api-gateway/`**: Gerencia o roteamento de requisições externas para os microsserviços internos correspondentes, lidando também com preocupações transversais (cross-cutting concerns) como rate limiting ou validação inicial de tokens.
- **`services/`**: Subdiretório que agrupa todos os microsserviços de backend. Cada microsserviço é estritamente isolado (tem seu próprio banco de dados lógico ou físico, dependências e `Dockerfile`).

### 2. `packages/`
Contém bibliotecas internas compartilhadas entre os microsserviços ou entre o frontend e backend (ex: definições de payloads/contratos de APIs, utilitários de log, wrappers de clientes HTTP). Evita a duplicação de código.

### 3. `docker/` e `docker-compose.yml`
- O `docker-compose.yml` na raiz serve para inicializar todo o ambiente local (bancos de dados, filas como RabbitMQ/Kafka, Redis, Gateway e os microsserviços) com um único comando: `docker compose up`.
- O diretório `docker/` guarda scripts adicionais de setup de banco de dados (`seed.sql`), arquivos de configuração de servidores (como `nginx.conf`) ou certs locais.

### 4. `docs/`
Reservada para manter o projeto auto-documentado. Contém fluxos de arquitetura, guias de engenharia de software, modelagem de dados e requisitos.