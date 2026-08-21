from fastapi import APIRouter, Depends, Query, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.auth import get_current_user
from app.database import get_db
from app.services.transaction_service import get_transactions, create_transaction, update_transaction, bulk_update_transactions, export_transactions_csv
from app.services.receipt_service import validate_receipt_file, upload_receipt_to_supabase
from app.schemas.transaction import TransactionListResponse, TransactionCreate, TransactionCreateResponse, TransactionResponse, TransactionUpdate, BulkUpdateBody
from app.schemas.split import SplitRequest, SplitListResponse
from app.services.split_service import create_splits, get_splits
from datetime import date
from decimal import Decimal
from typing import Optional, List
import uuid

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    account_id: Optional[uuid.UUID] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    amount_min: Optional[Decimal] = Query(None),
    amount_max: Optional[Decimal] = Query(None),
    search: Optional[str] = Query(None, max_length=200),
    pending: Optional[bool] = Query(None),
    tax_deductible: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transactions, total = await get_transactions(
        user_id=uuid.UUID(current_user["id"]),
        db=db,
        account_id=account_id,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        search=search,
        pending=pending,
        tax_deductible=tax_deductible,
        limit=limit,
        offset=offset,
    )
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=TransactionCreateResponse, status_code=201)
async def add_transaction(
    body: TransactionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        txn, warning = await create_transaction(
            user_id=uuid.UUID(current_user["id"]),
            data=body.model_dump(),
            db=db,
        )
        return {"transaction": txn, "duplicate_warning": warning}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/export")
async def export_transactions(
    start_date: date = Query(None),
    end_date: date = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    csv_content = await export_transactions_csv(
        uuid.UUID(current_user["id"]), db, start_date, end_date
    )
    filename = "transactions"
    if start_date:
        filename += f"_{start_date}"
    if end_date:
        filename += f"_to_{end_date}"
    filename += ".csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{transaction_id}/split", response_model=SplitListResponse, status_code=201)
async def split_transaction(
    transaction_id: uuid.UUID,
    body: SplitRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.transaction_service import get_transaction_by_id
    txn = await get_transaction_by_id(transaction_id, uuid.UUID(current_user["id"]), db)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    try:
        splits = await create_splits(
            transaction_id=transaction_id,
            user_id=uuid.UUID(current_user["id"]),
            splits=[s.model_dump() for s in body.splits],
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return {
        "splits": splits,
        "transaction_id": transaction_id,
        "original_amount": txn.amount,
    }


@router.post("/{transaction_id}/receipt", response_model=TransactionResponse)
async def upload_receipt(
    transaction_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.transaction_service import get_transaction_by_id
    txn = await get_transaction_by_id(transaction_id, uuid.UUID(current_user["id"]), db)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    file_bytes = await file.read()

    try:
        validate_receipt_file(file.content_type, len(file_bytes))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    storage_path = f"{current_user['id']}/{transaction_id}/{file.filename}"

    try:
        public_url = await upload_receipt_to_supabase(file_bytes, file.content_type, storage_path)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    txn.receipt_url = public_url
    await db.commit()
    await db.refresh(txn)
    return txn


@router.patch("/bulk", response_model=List[TransactionResponse])
async def bulk_edit_transactions(
    body: BulkUpdateBody,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        updated = await bulk_update_transactions(
            transaction_ids=[str(tid) for tid in body.transaction_ids],
            updates=body.updates.model_dump(exclude_unset=True),
            user_id=current_user["id"],
            db=db,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return updated


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def edit_transaction(
    transaction_id: uuid.UUID,
    body: TransactionUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    txn = await update_transaction(
        transaction_id=transaction_id,
        user_id=uuid.UUID(current_user["id"]),
        data=body.model_dump(exclude_unset=True),
        db=db,
    )
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
            headers={"X-Error-Code": "TRANSACTION_NOT_FOUND"},
        )
    return txn
