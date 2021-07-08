from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import Response, JSONResponse



from src.models.balance_models import (
    ExpenseEntry,
    SettlementEntry,
    Balance,
    ExpenseMaster
)

balance_router = APIRouter()

@balance_router.post("/balance/create_expense")
def create_expense(expense: ExpenseEntry):

    # Check the type of expense
    # validate if the division is right
    # create Expense master entries
    if expense.share_type == 0:
        total_percentage=0
        balance_entries=[]
        for key, val in expense.share_division.items():
            total_percentage = total_percentage+val
            balance_entry = Balance(
                payer=expense.user_id,
                payee=key,
                amount=expense.amount*val/100,
                currency=expense.currency
            )
            balance_entries.append(balance_entry)
        if total_percentage > 100:
            return JSONResponse(status_code=400, content="Count of total percventage is greater than 100")
    if expense.share_type == 1:
        total_value=0
        balance_entries=[]
        for key, val in expense.share_division.items():
            total_value = total_value+val
            balance_entry = Balance(
                payer=expense.user_id,
                payee=key,
                amount=val,
                currency=expense.currency
            )
            balance_entries.append(balance_entry)
        if total_value > expense.amount:
            return JSONResponse(status_code=400, content="Count of total percventage is greater than 100")
    print("To create balance_entries", balance_entries)
    for val in balance_entries:
        val.save()
    expense_master = ExpenseMaster(
            type_of_expense=0,
            amount=expense.amount,
            currency=expense.currency,
            created_by=expense.user_id,
            share_type=expense.share_type,
            share_division=expense.share_division
        )
    print("To create expense_master", expense_master)
    expense_master.save()

    return {"status": "ok"}

@balance_router.post("/balance/create_settlement")
def create_settlement(settlement: SettlementEntry):
    balance_entry = Balance(
        payer=settlement.payer,
        payee=settlement.payee,
        amount=settlement.amount,
        currency=settlement.currency
    )
    print("To create balance_entry", balance_entry)
    balance_entry.save()
    expense_master = ExpenseMaster(
            type_of_expense=1,
            amount=settlement.amount,
            currency=settlement.currency,
            created_by=settlement.payer
        )
    print("To create expense_master", expense_master)
    expense_master.save()

    return {"status": "ok"}

@balance_router.get("/balance")
def view_balance(user_id: str):
    # search for all the entries in which the passed user_id in in payer of payee
    # the payer entry total shall go into to_get
    # the payee entry total shall go into to_give
    to_get_balances = Balance.search_for_payer(user_id)
    total_to_get = 0
    for balance in to_get_balances:
        total_to_get = total_to_get + balance.amount
    to_give_balances = Balance.search_for_payee(user_id)
    total_to_give = 0
    for balance in to_give_balances:
        total_to_give = total_to_give + balance.amount
    return {"status": "ok", "total_to_get": total_to_get, "total_to_give": total_to_give}
