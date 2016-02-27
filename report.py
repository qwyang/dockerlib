import json
from pymongo import MongoClient


if __name__ == "__main__":
    config_file_path = "env.json"
    with open(config_file_path) as f:
        config = json.load(f)
    mongo_config = config["env"]["mongodb"]
    mongodb = MongoClient(mongo_config["url"])
    db = mongodb[mongo_config["database"]]
    collection = db[mongo_config["collection"]]
    print "-"*30 + "The following is the Environment information for The Test." + "-"*30
    print json.dumps(config["env"], indent=4)
    print "-"*30 + "The following is performance test result data." + "-"*30
    for document in collection.find():
        document.pop("_id")
        print json.dumps(document, indent=4)