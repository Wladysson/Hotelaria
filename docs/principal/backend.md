# Arquitetura de Backend (FastAPI + PostgreSQL + RabbitMQ)

Este documento define as diretrizes arquiteturais, a estrutura de pastas, os padrões de projeto, a estratégia de testes e as especificações de API para o desenvolvimento do **Sistema de Reservas de Rede Hoteleira**.

---

## 1. Estrutura de Diretórios e Divisão em Pacotes

Adotaremos a estrutura padrão de projetos Python gerenciados via **Poetry**, separando responsabilidades por meio de uma arquitetura modular em camadas dentro da pasta principal da aplicação (`app/`):

```text
├── docs/                      # Documentação do projeto (markdowns)
├── app/                       # Código-fonte da aplicação
│   ├── main.py                # Ponto de entrada (FastAPI App)
│   ├── core/                  # Configurações globais e segurança
│   │   ├── config.py          # Variáveis de ambiente (Pydantic Settings)
│   │   ├── database.py        # Conexão com Postgres (SQLAlchemy Session)
│   │   ├── security.py        # Hashing de senhas e geração de JWT
│   │   └── rabbitmq.py        # Configurações do cliente RabbitMQ
│   ├── models/                # Modelos ORM (SQLAlchemy)
│   │   ├── base.py            # Classe declarativa base
│   │   ├── cidade.py
│   │   ├── hotel.py
│   │   ├── quarto.py
│   │   ├── usuario.py
│   │   ├── reserva.py
│   │   └── ...
│   ├── schemas/               # Schemas de validação e serialização (Pydantic)
│   │   ├── cidade.py
│   │   ├── hotel.py
│   │   ├── usuario.py
│   │   └── reserva.py
│   ├── repositories/          # Abstração de acesso a dados (Queries SQLAlchemy)
│   ├── services/              # Camada de lógica de negócio e queries complexas
│   │   ├── reserva_service.py
│   │   └── ...
│   ├── api/                   # Controladores e Rotas da API REST
│   │   ├── deps.py            # Injeção de dependências (get_db, get_current_user)
│   │   └── v1/
│   │       ├── router.py      # Agrupador de rotas v1
│   │       ├── auth.py        # Login e geração de Token
│   │       ├── cidades.py
│   │       ├── hoteis.py
│   │       └── reservas.py
│   └── workers/               # Consumidores assíncronos (Celery/pika)
│       ├── worker.py          # Script de inicialização do Worker
│       └── tasks/             # Definição das tarefas em background
│           └── reserva_tasks.py
├── tests/                     # Testes automatizados (pytest)
│   ├── conftest.py            # Fixtures de teste (DB em memória, App mockado)
│   ├── api/                   # Testes das rotas HTTP
│   ├── services/              # Testes unitários de regras de negócio
│   └── workers/               # Testes de processamento de filas
├── pyproject.toml             # Dependências e empacotamento gerenciados pelo Poetry
├── Dockerfile                 # Build da imagem deste serviço
└── README.md
```

> [!NOTE]
> O `docker-compose.yml` que orquestra Postgres, MongoDB, RabbitMQ e os serviços fica na **raiz do monorepo**, não dentro do `core-service`. Veja [Estrutura de Diretórios](./estrutura_pastas.md).

---

## 2. Divisão de Responsabilidades (Camadas)

Para garantir facilidade de manutenção e testes independentes, a aplicação é dividida nas seguintes camadas de responsabilidade:

1. **Camada de Exposição (API - FastAPI Routes)**: Responsável por receber as requisições HTTP, delegar a lógica para os serviços correspondentes e retornar respostas estruturadas. Não deve conter lógica de banco direta ou regras de validação complexas.
2. **Camada de Validação e DTOs (Pydantic Schemas)**: Garante a tipagem, validação prévia dos dados de entrada (tipos, tamanhos, e-mails válidos) e a formatação adequada da saída (ocultando campos sensíveis como o hash da senha).
3. **Camada de Repositórios (Repositories)**: Isola o acesso a dados e consultas SQL/SQLAlchemy directas da camada de serviços, facilitando a troca de tecnologia ou realização de mocks.
4. **Camada de Negócio (Services)**: Centraliza as regras de negócio do sistema (ex: verificar se o número de hóspedes é compatível com o quarto). É a única camada que orquestra interações complexas entre múltiplos modelos de dados.
5. **Camada de Dados (SQLAlchemy Models)**: Representa o mapeamento direto das tabelas físicas do PostgreSQL. As migrations geradas pelo Alembic refletem exatamente esta pasta de modelos.
6. **Mensageria e Workers (RabbitMQ / Celery)**: Executa tarefas assíncronas em segundo plano que requerem alto tempo de processamento (processamento do pagamento e geração de documentos de confirmação), garantindo que o cliente receba a resposta HTTP quase instantaneamente.

---

## 3. Estratégia de Testes Unitários e de Integração

Utilizaremos o framework **pytest** com as seguintes diretrizes para garantir testes rápidos, isolados e confiáveis:

### Testes de Integração da API (pytest + TestClient do FastAPI)
* **Banco de Dados de Teste:** As consultas devem ser direcionadas a um banco de dados de teste isolado ou criado dinamicamente em memória (utilizando SQLite com suporte a UUIDs ou um container Postgres efêmero).
* **Isolamento de Transações:** Cada caso de teste deve rodar dentro de uma transação de banco de dados (`SAVEPOINT`) que sofre rollback automático ao final do teste, garantindo que um teste nunca polua o estado do banco para o teste seguinte.
* **Mocks de Serviços Externos:** O RabbitMQ e serviços externos de pagamento devem ser mockados (utilizando `pytest-mock`) para testar o comportamento da rota sem depender de brokers reais estarem ativos durante a suíte de testes.

### Testes Unitários de Regras de Negócio (Services)
* Focados em testar puramente as regras (ex: tentar reservar um quarto com data de check-out anterior à de check-in deve levantar um erro `ValueError` ou uma exceção HTTP personalizada).

---

## 4. Gerenciamento e Teste das Rotas (Swagger & Postman)

### Documentação Automática (Swagger UI)
A API do FastAPI gera automaticamente a especificação OpenAPI. Durante as aulas e revisões de Sprints, a principal ferramenta de testes manuais dos alunos será a interface do Swagger, disponível localmente em:
* `http://localhost:8000/docs` (Swagger interativo)
* `http://localhost:8000/redoc` (Documentação estática detalhada)

### Organização da Coleção do Postman
Para facilitar testes manuais em lote ou testes automatizados via CLI (Newman), os alunos devem organizar a coleção do Postman estruturada da seguinte forma:

1. **Variáveis de Ambiente (Environment)**:
   - `base_url`: `http://localhost:8000/api/v1`
   - `token`: Armazena dinamicamente o Token JWT após o login bem-sucedido.
2. **Estrutura de Pastas (Requests)**:
   - **`[1] Auth`**: Registro de usuário e Login (com script no Postman para salvar o token retornado na variável `{{token}}`).
   - **`[2] Cidades`**: Listagem, busca e cadastro (admin).
   - **`[3] Hotéis`**: Cadastro (admin) e listagem/filtros.
   - **`[4] Quartos`**: Cadastro de quartos por hotel (admin) e busca de quartos por capacidade/preço.
   - **`[5] Reservas`**: Solicitação de reserva, consulta de status e listagem de reservas do usuário logado.
   - **`[6] Serviços Adicionais`**: Cadastro de serviços (admin) e listagem.
   - **`[7] Avaliações`**: Criação de avaliações após estadia.