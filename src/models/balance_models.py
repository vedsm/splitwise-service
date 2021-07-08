from pydantic import BaseModel
from typing import List, Dict, Optional


from src.dao.db_config import (
    myclient,
    mydb,
)

balance_collection = mydb.splitwise_balance
expense_master_collection = mydb.splitwise_expence_master

# class User(BaseModel):
#     name: str
#     # description: Optional[str] = None

#     def save(cls):
#         print("saving user", cls.dict())
#         created_user = user_collection.insert_one(cls.dict())
#         created_user_id = created_user.inserted_id
#         return str(created_user_id)


class ExpenseEntry(BaseModel):
    user_id: str
    share_type: int
    share_division: Dict
    amount: int
    currency: Optional[str] = "INR"

class SettlementEntry(BaseModel):
    payer: str
    payee: str
    amount: int
    currency: Optional[str] = "INR"

class Balance(BaseModel):
    payer: str
    payee: str
    amount: int
    currency: Optional[str] = "INR"

    def save(cls):
        print("saving balance", cls.dict())
        created_balance = balance_collection.insert_one(cls.dict())
        created_balance_id = created_balance.inserted_id
        return str(created_balance_id)
    
    def search_for_payer(user_id):
        balances = list(balance_collection.find({"payer": str(user_id)}))
        print("found balances", balances, user_id)
        return_balances = []
        for balance in balances:
            return_balances.append(Balance(**balance))
        print("found return_balances", return_balances)
        return return_balances

    def search_for_payee(user_id):
        balances = list(balance_collection.find({"payee": str(user_id)}))
        print("found balances", balances, user_id)
        return_balances = []
        for balance in balances:
            return_balances.append(Balance(**balance))
        print("found return_balances", return_balances)
        return return_balances

class ExpenseMaster(BaseModel):
    type_of_expense: int
    amount: int
    currency: Optional[str] = "INR"
    created_by: str
    share_type: Optional[int]
    share_division: Optional[Dict]

    def save(cls):
        print("saving expense_master", cls.dict())
        created_expense_master = expense_master_collection.insert_one(cls.dict())
        created_expense_master_id = created_expense_master.inserted_id
        return str(created_expense_master_id)
