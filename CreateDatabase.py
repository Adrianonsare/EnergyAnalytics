from pymongo import ASCENDING


def get_database():
    from pymongo import MongoClient
    import pymongo
    import passkey

    client = pymongo.MongoClient("mongodb+srv://%s:%s@cluster0.r3enc.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"% (
    passkey.username, passkey.password))

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    # Create the database for our example (we will use the same database throughout the tutorial
    return client['EnergyData']
    
# This is added so that many files can reuse the function get_database()
if __name__ == "__main__":    
    
    # Get the database
    dbname = get_database()
dbname=get_database()
collection_name = dbname["Lake_Turkana"]
# collection_name.create_index([("idx",ASCENDING)],unique=True  )