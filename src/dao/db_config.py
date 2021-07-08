import os
import pymongo

MONGO_CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_STRING", None)

myclient = pymongo.MongoClient(MONGO_CONNECTION_STRING)
mydb = myclient.get_default_database()





# TESTING = os.environ.get("TESTING", "FALSE")
# if TESTING == "FALSE":
#     myclient = pymongo.MongoClient(MONGO_CONNECTION_STRING)
# else:
#     myclient = mongomock.MongoClient()
