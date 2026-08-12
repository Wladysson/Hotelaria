apps/
└── services/
    └── auth-service/
        │
        ├── app/
        │   ├── main.py
        │   │
        │   ├── core/
        │   │   ├── config.py
        │   │   ├── database.py
        │   │   ├── security.py
        │   │   └── exceptions.py
        │   │
        │   ├── models/
        │   │   ├── __init__.py
        │   │   ├── base.py
        │   │   └── usuario.py
        │   │
        │   ├── schemas/
        │   │   ├── __init__.py
        │   │   ├── auth.py
        │   │   └── usuario.py
        │   │
        │   ├── repositories/
        │   │   ├── __init__.py
        │   │   └── usuario_repository.py
        │   │
        │   ├── services/
        │   │   ├── __init__.py
        │   │   ├── auth_service.py
        │   │   └── usuario_service.py
        │   │
        │   └── api/
        │       ├── __init__.py
        │       ├── deps.py
        │       └── v1/
        │           ├── __init__.py
        │           ├── router.py
        │           ├── auth.py
        │           └── usuarios.py
        │
        ├── alembic/
        │   ├── versions/
        │   │   └── .gitkeep
        │   ├── env.py
        │   ├── script.py.mako
        │   └── README
        │
        ├── tests/
        │   ├── __init__.py
        │   ├── conftest.py
        │   ├── api/
        │   │   ├── test_auth.py
        │   │   └── test_usuarios.py
        │   └── services/
        │       ├── test_auth_service.py
        │       └── test_usuario_service.py
        │
        ├── .dockerignore
        ├── Dockerfile
        ├── alembic.ini
        ├── env_example
        ├── poetry.toml
        ├── pyproject.toml
        ├── poetry.lock
        ├── requirements.txt
        ├── README.md
        └── ruff.toml