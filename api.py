from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cloudflare import Cloudflare
import os

app = FastAPI()

# Add this after initializing FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, change this for security
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

API_TOKEN = os.getenv("API_TOKEN")
DB_ID = os.getenv("DB_ID")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

def get_client():
    client = Cloudflare(
    # api_email=os.environ.get("CLOUDFLARE_EMAIL"),  # This is the default and can be omitted
        api_token=API_TOKEN  # This is the default and can be omitted
    )
    return client

def execute_query(client, query):
  
    page = client.d1.database.query(
    database_id=DB_ID,
    account_id=ACCOUNT_ID,
    sql=query,
    )  
    return page[0]

@app.get("/images")
def get_images(folder: str = None, selected: bool = None, page: int = 1, limit: int = 9):
    client = get_client()
    offset = (page - 1) * limit

    query = "SELECT * FROM images WHERE 1=1"
    if folder:
        query += f" AND folder = '{folder}'"
    if selected:
        query += f" AND is_selected = {int(selected)}"
    else:
        query += f" LIMIT {limit} OFFSET {offset};"
    result = execute_query(client, query)
    return [{"id": row["id"], "name": row["name"], "folder": row["folder"], "is_selected": row["is_selected"], "link": row["link"]} for row in result.results]

@app.get("/folders")
def get_folders():
    client = get_client()
    query = "SELECT DISTINCT folder FROM images;"
    result = execute_query(client, query)
    return [row['folder'] for row in result.results]

@app.post("/select/{image_id}")
def toggle_selection(image_id: int):
    client = get_client()
    query = f"UPDATE images SET is_selected = NOT is_selected WHERE id = {image_id};"
    execute_query(client, query)
    return {"message": "Updated successfully"}

@app.get("/selected_count")
def get_total_selected_count():
    client = get_client()
    query = "SELECT COUNT(*) as count FROM images WHERE is_selected = 1;"
    result = execute_query(client, query)
    return {"total_selected": result.results[0]['count']}