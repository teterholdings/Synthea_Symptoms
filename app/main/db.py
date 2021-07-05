import pymongo
from contextlib import contextmanager

def connect(
    uri: str = "localhost",
    port: int = 27017,
    db_name: str = 'symptoms_db'
):
    """
    Function to connect to Mongo DB instance. 

    Args:
        uri: (str) uri to mongo instance
        port: (int) port number mongo is listening on
        db_name: (str) name of database to use

    Returns:
        pymongo.database.Database object

    """
    client = pymongo.MongoClient(
        uri,
        port
    )
    return client

@contextmanager
def symptoms_db():
    try:
        client = connect()
        db = client.symptoms_db
        yield db
    finally:
        client.close()


