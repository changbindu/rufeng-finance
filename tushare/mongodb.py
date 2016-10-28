import json
import datetime
import pandas as pd
from pymongo import MongoClient
import tushare as ts

client = MongoClient('localhost', 27017)
db = client.test_database
hist_data = db.hist_data


# Make a query to the specific DB and Collection
cursor = hist_data.find({'code': '600848'})
if (cursor.count() > 0):
    doc = cursor[0]
    doc['last_update'] = datetime.datetime.utcnow()
    hist_data.save(doc)
    print('updated document id ' + str(doc['_id']))

    # read today's data
    cursor = hist_data.find({'code': '600848', datetime.datetime.now().strftime('%Y-%m-%d'): {'$exists':True}})
    # Expand the cursor and construct the DataFrame
    df = pd.DataFrame(list(cursor))
    print(df)
else:
    df = ts.get_hist_data('600848')
    id = hist_data.insert_one(df.to_dict(orient='index')).inserted_id
    hist_data.update({'_id': id}, {'$set': {'code': '600848'}})
    print('inserted new document id ' + str(id))
