from pymongo import MongoClient

# --- 本地MongoDB示例 ---
client = MongoClient("mongodb://crossborder:4ce5af6c@47.113.231.122:27017/")

# --- 如果是MongoDB Atlas云数据库 ---
# client = MongoClient("mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority")

# 选择数据库（如果没有会自动创建）
db = client['my_database']

# 选择集合（表格的概念，如果没有也会自动创建）
collection = db['my_collection']

# 插入一条数据
data = {"name": "Alice", "age": 25}
result = collection.insert_one(data)
print(f"Inserted id: {result.inserted_id}")

# 查询数据
for item in collection.find():
    print(item)
