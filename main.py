from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os

app = FastAPI()

# MongoDB connection setup
MONGODB_URL = "mongodb://localhost:27017"  # You can move this to .env file
client = AsyncIOMotorClient(MONGODB_URL)
db = client.item_database  # database name
collection = db.items  # collection name

class Item(BaseModel):
    name: str
    price: float
    quantity: int

# MongoDB operations
@app.on_event("startup")
async def startup_db_client():
    try:
        # Verify the connection
        await client.admin.command('ping')
        print("Successfully connected to MongoDB")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.post("/items/{item_id}")
async def create_item(item_id: int, item: Item):
    # Check if item already exists
    if await collection.find_one({"_id": item_id}):
        raise HTTPException(status_code=400, detail="Item already exists")
    
    # Create new item
    item_dict = item.dict()
    item_dict["_id"] = item_id
    await collection.insert_one(item_dict)
    return {"message": "Item created successfully", "item": item_dict}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await collection.find_one({"_id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/items/")
async def get_all_items():
    items = []
    cursor = collection.find({})
    async for document in cursor:
        items.append(document)
    return items

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    # Check if item exists
    if not await collection.find_one({"_id": item_id}):
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update item
    item_dict = item.dict()
    await collection.update_one(
        {"_id": item_id},
        {"$set": item_dict}
    )
    
    updated_item = await collection.find_one({"_id": item_id})
    return {"message": "Item updated successfully", "item": updated_item}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    # Check if item exists
    result = await collection.delete_one({"_id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}