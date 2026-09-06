import os
from collections.abc import AsyncGenerator, Generator
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.database import get_db_session
from src.main import app
from src.models.base import Base


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://payment:payment@localhost:5440/payment_test",
)


@pytest.fixture
def test_app() -> FastAPI:
    """
    Retorna a aplicação FastAPI utilizada pelos testes.
    """

    return app


@pytest.fixture
def fake_uuid():
    """
    Gera identificadores UUID para os testes.
    """

    return uuid4


@pytest.fixture
def fake_amount() -> Decimal:
    """
    Retorna um valor monetário padrão para os testes.
    """

    return Decimal("150.00")


@pytest.fixture
def fake_currency() -> str:
    return "BRL"


@pytest.fixture
def fake_reservation_id():
    return uuid4()


@pytest.fixture
def fake_customer_id():
    return uuid4()


@pytest.fixture
def fake_payment_method_id():
    return uuid4()


@pytest.fixture
def fake_transaction_id():
    return uuid4()


@pytest.fixture
def fake_refund_id():
    return uuid4()


@pytest.fixture
def payment_payload(
    fake_reservation_id,
    fake_customer_id,
    fake_payment_method_id,
) -> dict:
    """
    Payload padrão para criação de pagamentos.
    """

    return {
        "reservation_id": str(fake_reservation_id),
        "customer_id": str(fake_customer_id),
        "amount": "150.00",
        "currency": "BRL",
        "payment_method_id": str(fake_payment_method_id),
        "provider": "stripe",
        "description": "Pagamento de reserva",
        "requires_capture": False,
        "idempotency_key": f"payment-{uuid4()}",
        "metadata": {
            "source": "test",
        },
    }


@pytest.fixture
def refund_payload(
    fake_transaction_id,
    fake_reservation_id,
) -> dict:
    """
    Payload padrão para criação de reembolsos.
    """

    return {
        "transaction_id": str(fake_transaction_id),
        "reservation_id": str(fake_reservation_id),
        "amount": "50.00",
        "reason": "customer_request",
        "idempotency_key": f"refund-{uuid4()}",
        "description": "Reembolso de teste",
    }


@pytest.fixture
def mock_gateway_response() -> dict:
    """
    Resposta normalizada de gateway utilizada nos testes unitários.
    """

    return {
        "id": "gateway-tx-test-001",
        "gateway_transaction_id": "gateway-tx-test-001",
        "status": "succeeded",
        "captured_amount": Decimal("150.00"),
        "raw_response": {},
    }


@pytest.fixture
def mock_refund_gateway_response() -> dict:
    """
    Resposta normalizada de reembolso utilizada nos testes.
    """

    return {
        "id": "gateway-refund-test-001",
        "gateway_refund_id": "gateway-refund-test-001",
        "status": "succeeded",
        "raw_response": {},
    }


@pytest.fixture
def test_engine():
    """
    Cria engine assíncrono isolado para testes de integração.

    A fixture só será utilizada pelos testes que realmente
    precisarem de banco de dados.
    """

    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    yield engine

    # O encerramento assíncrono é realizado pela fixture abaixo.


@pytest_asyncio.fixture
async def test_database_engine():
    """
    Cria e encerra o engine assíncrono utilizado nos testes.
    """

    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def setup_database(
    test_database_engine,
) -> AsyncGenerator[None, None]:
    """
    Cria as tabelas necessárias para o teste e remove-as ao final.

    Essa fixture deve ser utilizada somente em testes de integração.
    """

    async with test_database_engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    try:
        yield
    finally:
        async with test_database_engine.begin() as connection:
            await connection.run_sync(
                Base.metadata.drop_all
            )


@pytest_asyncio.fixture
async def db_session(
    test_database_engine,
    setup_database,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Fornece uma sessão isolada para testes de integração.
    """

    session_factory = async_sessionmaker(
        bind=test_database_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client(
    test_app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP assíncrono para testes E2E da aplicação.
    """

    transport = ASGITransport(
        app=test_app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as async_client:
        yield async_client


@pytest_asyncio.fixture
async def authenticated_client(
    test_app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP autenticado para testes E2E.

    O token utilizado aqui é propositalmente fictício.
    """

    transport = ASGITransport(
        app=test_app,
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={
            "Authorization": "Bearer test-access-token",
        },
    ) as async_client:
        yield async_client


@pytest.fixture
def override_database_dependency(
    test_app: FastAPI,
    db_session: AsyncSession,
) -> Generator[None, None, None]:
    """
    Substitui a dependência de banco da aplicação durante o teste.
    """

    async def override_get_db_session():
        yield db_session

    test_app.dependency_overrides[
        get_db_session
    ] = override_get_db_session

    try:
        yield
    finally:
        test_app.dependency_overrides.pop(
            get_db_session,
            None,
        )