from pydantic import BaseModel

from src.dao.db_config import (
    myclient,
    mydb,
)

user_collection = mydb.splitwise_user

class User(BaseModel):
    name: str
    # description: Optional[str] = None

    def save(cls):
        print("saving user", cls.dict())
        created_user = user_collection.insert_one(cls.dict())
        created_user_id = created_user.inserted_id
        return str(created_user_id)

