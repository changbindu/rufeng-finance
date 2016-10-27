import json
import pandas as pd
from pymongo import MongoClient
import tushare as ts

client = MongoClient('localhost', 27017)
db = client.test_database
hist_data = db.hist_data

df = ts.get_hist_data('600848')
id = hist_data.insert_one(df.to_dict(orient='index')).inserted_id
print('inserted new document id ' + str(id))

hist_data.update({'_id': id},{'$set': {'code':'600848'}})

# Make a query to the specific DB and Collection
cursor = hist_data.find({})
# Expand the cursor and construct the DataFrame
df =  pd.DataFrame(list(cursor))