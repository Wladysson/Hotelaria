from decimal import Decimal
from uuid import uuid4

import pytest

from src.models.transactions import (
    PaymentProvider,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from src.repositories.transactions_repository import TransactionRepository


def build_transaction(
    *,
    customer_id=None,
    reservation_id=None,
    status=TransactionStatus.PENDING,
    amount=Decimal("150.00"),
    idempotency_key=None,
    gateway_transaction_id=None,
):
    return Transaction(
        customer_id=customer_id or uuid4(),
        reservation_id=reservation_id or uuid4(),
        amount=amount,
        currency="BRL",
        transaction_type=TransactionType.PAYMENT,
        status=status,
        provider=PaymentProvider.STRIPE,
        gateway_transaction_id=gateway_transaction_id,
        idempotency_key=idempotency_key or f"payment-{uuid4()}",
        description="Transação de teste",
        requires_capture=False,
        captured_amount=Decimal("0.00"),
        refunded_amount=Decimal("0.00"),
        metadata_json={
            "source": "integration-test",
        },
    )


@pytest.mark.asyncio
async def test_create_transaction(db_session):
    repository = TransactionRepository(db_session)

    transaction = build_transaction()

    result = await repository.create(transaction)

    assert result.id is not None
    assert result.customer_id == transaction.customer_id
    assert result.reservation_id == transaction.reservation_id
    assert result.amount == Decimal("150.00")
    assert result.currency == "BRL"
    assert result.status == TransactionStatus.PENDING


@pytest.mark.asyncio
async def test_get_by_id_returns_transaction(db_session):
    repository = TransactionRepository(db_session)

    transaction = build_transaction()
    await repository.create(transaction)
    await db_session.commit()

    result = await repository.get_by_id(transaction.id)

    assert result is not None
    assert result.id == transaction.id
    assert result.idempotency_key == transaction.idempotency_key


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_transaction_does_not_exist(
    db_session,
):
    repository = TransactionRepository(db_session)

    result = await repository.get_by_id(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_by_idempotency_key_returns_transaction(db_session):
    repository = TransactionRepository(db_session)

    idempotency_key = f"payment-{uuid4()}"
    transaction = build_transaction(
        idempotency_key=idempotency_key,
    )

    await repository.create(transaction)
    await db_session.commit()

    result = await repository.get_by_idempotency_key(
        idempotency_key,
    )

    assert result is not None
    assert result.id == transaction.id
    assert result.idempotency_key == idempotency_key


@pytest.mark.asyncio
async def test_get_by_idempotency_key_returns_none_when_not_found(
    db_session,
):
    repository = TransactionRepository(db_session)

    result = await repository.get_by_idempotency_key(
        "non-existent-idempotency-key",
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_by_gateway_transaction_id_returns_transaction(
    db_session,
):
    repository = TransactionRepository(db_session)

    gateway_transaction_id = f"gateway-{uuid4()}"
    transaction = build_transaction(
        gateway_transaction_id=gateway_transaction_id,
    )

    await repository.create(transaction)
    await db_session.commit()

    result = await repository.get_by_gateway_transaction_id(
        gateway_transaction_id,
    )

    assert result is not None
    assert result.id == transaction.id
    assert (
        result.gateway_transaction_id
        == gateway_transaction_id
    )


@pytest.mark.asyncio
async def test_get_by_gateway_transaction_id_returns_none_when_not_found(
    db_session,
):
    repository = TransactionRepository(db_session)

    result = await repository.get_by_gateway_transaction_id(
        "non-existent-gateway-id",
    )

    assert result is None


@pytest.mark.asyncio
async def test_list_by_customer_returns_only_customer_transactions(
    db_session,
):
    repository = TransactionRepository(db_session)

    customer_id = uuid4()

    first = build_transaction(
        customer_id=customer_id,
        amount=Decimal("100.00"),
    )
    second = build_transaction(
        customer_id=customer_id,
        amount=Decimal("200.00"),
    )
    other_customer = build_transaction(
        customer_id=uuid4(),
        amount=Decimal("300.00"),
    )

    await repository.create(first)
    await repository.create(second)
    await repository.create(other_customer)
    await db_session.commit()

    result = await repository.list_by_customer(
        customer_id,
    )

    assert len(result) == 2
    assert {transaction.id for transaction in result} == {
        first.id,
        second.id,
    }


@pytest.mark.asyncio
async def test_list_by_customer_applies_pagination(db_session):
    repository = TransactionRepository(db_session)

    customer_id = uuid4()

    transactions = [
        build_transaction(
            customer_id=customer_id,
            amount=Decimal(f"{100 + index}.00"),
        )
        for index in range(5)
    ]

    for transaction in transactions:
        await repository.create(transaction)

    await db_session.commit()

    first_page = await repository.list_by_customer(
        customer_id,
        offset=0,
        limit=2,
    )

    second_page = await repository.list_by_customer(
        customer_id,
        offset=2,
        limit=2,
    )

    assert len(first_page) == 2
    assert len(second_page) == 2

    first_ids = {transaction.id for transaction in first_page}
    second_ids = {transaction.id for transaction in second_page}

    assert first_ids.isdisjoint(second_ids)


@pytest.mark.asyncio
async def test_list_by_reservation_returns_only_reservation_transactions(
    db_session,
):
    repository = TransactionRepository(db_session)

    reservation_id = uuid4()

    first = build_transaction(
        reservation_id=reservation_id,
    )
    second = build_transaction(
        reservation_id=reservation_id,
    )
    other_reservation = build_transaction(
        reservation_id=uuid4(),
    )

    await repository.create(first)
    await repository.create(second)
    await repository.create(other_reservation)
    await db_session.commit()

    result = await repository.list_by_reservation(
        reservation_id,
    )

    assert len(result) == 2
    assert {transaction.id for transaction in result} == {
        first.id,
        second.id,
    }


@pytest.mark.asyncio
async def test_list_by_reservation_applies_pagination(
    db_session,
):
    repository = TransactionRepository(db_session)

    reservation_id = uuid4()

    transactions = [
        build_transaction(
            reservation_id=reservation_id,
        )
        for _ in range(5)
    ]

    for transaction in transactions:
        await repository.create(transaction)

    await db_session.commit()

    result = await repository.list_by_reservation(
        reservation_id,
        offset=1,
        limit=2,
    )

    assert len(result) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "transaction_status",
    [
        TransactionStatus.PENDING,
        TransactionStatus.AUTHORIZED,
        TransactionStatus.PROCESSING,
        TransactionStatus.SUCCEEDED,
        TransactionStatus.FAILED,
        TransactionStatus.CANCELLED,
    ],
)
async def test_list_by_status_filters_correctly(
    db_session,
    transaction_status,
):
    repository = TransactionRepository(db_session)

    matching_transaction = build_transaction(
        status=transaction_status,
    )

    different_transaction = build_transaction(
        status=(
            TransactionStatus.SUCCEEDED
            if transaction_status != TransactionStatus.SUCCEEDED
            else TransactionStatus.FAILED
        ),
    )

    await repository.create(matching_transaction)
    await repository.create(different_transaction)
    await db_session.commit()

    result = await repository.list_by_status(
        transaction_status,
    )

    assert len(result) == 1
    assert result[0].id == matching_transaction.id
    assert result[0].status == transaction_status


@pytest.mark.asyncio
async def test_list_by_status_applies_pagination(db_session):
    repository = TransactionRepository(db_session)

    status = TransactionStatus.PROCESSING

    for _ in range(5):
        await repository.create(
            build_transaction(status=status)
        )

    await db_session.commit()

    result = await repository.list_by_status(
        status,
        offset=1,
        limit=2,
    )

    assert len(result) == 2
    assert all(
        transaction.status == status
        for transaction in result
    )


@pytest.mark.asyncio
async def test_count_by_customer_returns_correct_count(
    db_session,
):
    repository = TransactionRepository(db_session)

    customer_id = uuid4()

    for _ in range(3):
        await repository.create(
            build_transaction(
                customer_id=customer_id,
            )
        )

    await repository.create(
        build_transaction(
            customer_id=uuid4(),
        )
    )

    await db_session.commit()

    result = await repository.count_by_customer(
        customer_id,
    )

    assert result == 3


@pytest.mark.asyncio
async def test_count_by_customer_returns_zero_when_empty(
    db_session,
):
    repository = TransactionRepository(db_session)

    result = await repository.count_by_customer(
        uuid4(),
    )

    assert result == 0


@pytest.mark.asyncio
async def test_count_by_reservation_returns_correct_count(
    db_session,
):
    repository = TransactionRepository(db_session)

    reservation_id = uuid4()

    for _ in range(4):
        await repository.create(
            build_transaction(
                reservation_id=reservation_id,
            )
        )

    await repository.create(
        build_transaction(
            reservation_id=uuid4(),
        )
    )

    await db_session.commit()

    result = await repository.count_by_reservation(
        reservation_id,
    )

    assert result == 4


@pytest.mark.asyncio
async def test_count_by_reservation_returns_zero_when_empty(
    db_session,
):
    repository = TransactionRepository(db_session)

    result = await repository.count_by_reservation(
        uuid4(),
    )

    assert result == 0


@pytest.mark.asyncio
async def test_update_transaction_status(db_session):
    repository = TransactionRepository(db_session)

    transaction = build_transaction(
        status=TransactionStatus.PENDING,
    )

    await repository.create(transaction)
    await db_session.commit()

    result = await repository.update(
        transaction,
        status=TransactionStatus.SUCCEEDED,
    )

    await db_session.commit()

    assert result.status == TransactionStatus.SUCCEEDED

    persisted = await repository.get_by_id(
        transaction.id,
    )

    assert persisted is not None
    assert persisted.status == TransactionStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_update_transaction_multiple_fields(
    db_session,
):
    repository = TransactionRepository(db_session)

    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    await repository.create(transaction)
    await db_session.commit()

    gateway_transaction_id = f"gateway-{uuid4()}"

    result = await repository.update(
        transaction,
        status=TransactionStatus.SUCCEEDED,
        gateway_transaction_id=gateway_transaction_id,
        captured_amount=Decimal("150.00"),
        failure_code=None,
        failure_message=None,
    )

    await db_session.commit()

    assert result.status == TransactionStatus.SUCCEEDED
    assert (
        result.gateway_transaction_id
        == gateway_transaction_id
    )
    assert result.captured_amount == Decimal("150.00")


@pytest.mark.asyncio
async def test_update_ignores_unknown_fields(db_session):
    repository = TransactionRepository(db_session)

    transaction = build_transaction()

    await repository.create(transaction)
    await db_session.commit()

    original_status = transaction.status

    result = await repository.update(
        transaction,
        status=TransactionStatus.SUCCEEDED,
        field_that_does_not_exist="ignored",
    )

    await db_session.commit()

    assert result.status == TransactionStatus.SUCCEEDED
    assert not hasattr(
        result,
        "field_that_does_not_exist",
    )
    assert original_status == TransactionStatus.PENDING


@pytest.mark.asyncio
async def test_delete_transaction(db_session):
    repository = TransactionRepository(db_session)

    transaction = build_transaction()

    await repository.create(transaction)
    await db_session.commit()

    transaction_id = transaction.id

    await repository.delete(transaction)
    await db_session.commit()

    result = await repository.get_by_id(
        transaction_id,
    )

    assert result is None


@pytest.mark.asyncio
async def test_delete_does_not_affect_other_transactions(
    db_session,
):
    repository = TransactionRepository(db_session)

    first = build_transaction()
    second = build_transaction()

    await repository.create(first)
    await repository.create(second)
    await db_session.commit()

    await repository.delete(first)
    await db_session.commit()

    deleted = await repository.get_by_id(first.id)
    remaining = await repository.get_by_id(second.id)

    assert deleted is None
    assert remaining is not None
    assert remaining.id == second.id


@pytest.mark.asyncio
async def test_repository_preserves_decimal_precision(
    db_session,
):
    repository = TransactionRepository(db_session)

    transaction = build_transaction(
        amount=Decimal("123456789012345.67"),
    )

    await repository.create(transaction)
    await db_session.commit()

    result = await repository.get_by_id(
        transaction.id,
    )

    assert result is not None
    assert result.amount == Decimal(
        "123456789012345.67"
    )


@pytest.mark.asyncio
async def test_repository_persists_metadata(
    db_session,
):
    repository = TransactionRepository(db_session)

    transaction = build_transaction()
    transaction.metadata_json = {
        "source": "hotel-service",
        "channel": "web",
        "attempt": "2",
    }

    await repository.create(transaction)
    await db_session.commit()

    result = await repository.get_by_id(
        transaction.id,
    )

    assert result is not None
    assert result.metadata_json == {
        "source": "hotel-service",
        "channel": "web",
        "attempt": "2",
    }