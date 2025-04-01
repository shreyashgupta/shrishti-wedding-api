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

bride_auth = {
    "API_TOKEN": os.getenv("API_TOKEN"),
    "DB_ID": os.getenv("DB_ID"),
    "ACCOUNT_ID": os.getenv("ACCOUNT_ID"),
}

groom_auth = {
    "API_TOKEN": os.getenv("GROOM_API_TOKEN"),
    "DB_ID": os.getenv("GROOM_DB_ID"),
    "ACCOUNT_ID": os.getenv("GROOM_ACCOUNT_ID"),
}


def get_auth(user_type: str):
    if user_type == "groom":
        return groom_auth
    return bride_auth


def execute_query(auth, query):
    client = Cloudflare(api_token=auth["API_TOKEN"])
    page = client.d1.database.query(
        database_id=auth["DB_ID"],
        account_id=auth["ACCOUNT_ID"],
        sql=query,
    )
    return page.result[0]


@app.get("/images")
def get_images(
    folder: str = None,
    selected: bool = None,
    page: int = 1,
    limit: int = 9,
    user_type: str = "",
):
    offset = (page - 1) * limit

    query = "SELECT * FROM images WHERE 1=1"
    if folder:
        query += f" AND folder = '{folder}'"
    if selected:
        query += f" AND is_selected = {int(selected)}"
    if limit:
        query += f" LIMIT {limit} OFFSET {offset};"

    result = execute_query(get_auth(user_type), query)
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "folder": row["folder"],
            "is_selected": row["is_selected"],
            "link": row["link"],
        }
        for row in result.results
    ]


@app.get("/folders")
def get_folders():
    query = "SELECT DISTINCT folder FROM images;"
    result = execute_query(get_auth(""), query)
    return [row["folder"] for row in result.results]


@app.post("/select/{image_id}")
def toggle_selection(image_id: int, user_type: str = ""):
    query = f"UPDATE images SET is_selected = true WHERE id = {image_id};"
    execute_query(get_auth(user_type), query)
    return {"message": "Updated successfully"}


@app.post("/deselect/{image_id}")
def toggle_selection(image_id: int, user_type: str = ""):
    query = f"UPDATE images SET is_selected = false WHERE id = {image_id};"
    execute_query(get_auth(user_type), query)
    return {"message": "Updated successfully"}


@app.get("/selected_count")
def get_total_selected_count(user_type: str = "", folder: str = None):
    query = "SELECT COUNT(*) as count FROM images WHERE is_selected = 1"
    if folder:
        query += f" AND folder = '{folder}'"
    result = execute_query(get_auth(user_type), query)
    return {"total_selected": result.results[0]["count"]}
