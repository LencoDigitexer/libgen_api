from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import re
from libgen_api import LibgenSearch

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*" allows all domains, you can specify a list of domains instead
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Initialize the LibgenSearch object
searcher = LibgenSearch()

# Pydantic models
class Filter(BaseModel):
    field: str
    value: str
    exact_match: Optional[bool] = True

class SearchRequest(BaseModel):
    query: str
    filters: Optional[List[Filter]] = None

@app.get("/search/title", response_model=List[Dict])
def search_by_title(query: str):
    """Perform a basic search by title."""
    if len(query) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters long.")
    results = searcher.search_title(query)
    print(results)
    return results

@app.get("/search/author", response_model=List[Dict])
def search_by_author(query: str):
    """Perform a basic search by author."""
    if len(query) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters long.")
    results = searcher.search_author(query)
    return results

@app.post("/search/title/filtered", response_model=List[Dict])
def search_title_filtered(request: SearchRequest):
    """Perform a filtered search by title."""
    if len(request.query) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters long.")
    filters = {filter.field: filter.value for filter in request.filters or []}
    exact_match = all(filter.exact_match for filter in request.filters or [])
    results = searcher.search_title_filtered(request.query, filters, exact_match=exact_match)
    return results

@app.post("/search/author/filtered", response_model=List[Dict])
def search_author_filtered(request: SearchRequest):
    """Perform a filtered search by author."""
    if len(request.query) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters long.")
    filters = {filter.field: filter.value for filter in request.filters or []}
    exact_match = all(filter.exact_match for filter in request.filters or [])
    results = searcher.search_author_filtered(request.query, filters, exact_match=exact_match)
    return results

@app.post("/resolve", response_model=Dict[str, str])
def resolve_download_links(item: Dict):
    """Resolve the mirror links for a given item to direct download links."""
    try:
        download_links = searcher.resolve_download_links(item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving download links: {str(e)}")
    return download_links

@app.get("/columns", response_model=List[str])
def get_column_names():
    """Return the list of available filterable fields."""
    col_names = [
        "ID", "Author", "Title", "Publisher", "Year", "Pages", "Language",
        "Size", "Extension", "Mirror_1", "Mirror_2", "Mirror_3", "Mirror_4", "Mirror_5", "Edit"
    ]
    return col_names

@app.get("/", response_model=Dict)
def root():
    return {
        "message": "Welcome to the Libgen API! Use /docs for the interactive API documentation.",
        "endpoints": [
            "/search/title",
            "/search/author",
            "/search/title/filtered",
            "/search/author/filtered",
            "/resolve",
            "/columns"
        ]
    }

@app.get("/download")
async def download_file(file_url: str):
    """Proxy file download through your server."""
    # Validate the URL (simple regex check for expected format)
    if not re.match(r'https://download.library.gift/main/\d+/[a-f0-9]+/.+', file_url):
        raise HTTPException(status_code=400, detail="Invalid download link format.")

    try:
        async with httpx.AsyncClient() as client:
            # Send GET request to the file's URL
            response = await client.get(file_url)
            response.raise_for_status()  # Raise exception for bad responses (e.g., 404, 500)

            # Return the file as a response with correct headers
            headers = {'Content-Disposition': f'attachment; filename="{file_url.split("/")[-1]}"'}
            return Response(content=response.content, media_type="application/pdf", headers=headers)

    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {exc}")

    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Error downloading file: {exc.response.text}")
