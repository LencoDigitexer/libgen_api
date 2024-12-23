from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from libgen_api import LibgenSearch

app = FastAPI()

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
