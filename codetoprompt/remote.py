"""Handles fetching and processing of remote URL targets."""

import re
import requests
from io import BytesIO
from typing import Dict, Any, List
from urllib.parse import urlparse
from pathlib import Path

from bs4 import BeautifulSoup, Comment
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi

from .utils import EXT_TO_LANG

# Constants for GitHub processing
EXCLUDED_DIRS = ["dist", "node_modules", ".git", "__pycache__", ".vscode", ".idea"]
ALLOWED_EXTENSIONS = set(k for k, v in EXT_TO_LANG.items() if v)


def get_url_type(url: str) -> str:
    """Determines the type of URL."""
    parsed_url = urlparse(url)
    if "github.com" in parsed_url.netloc:
        return "github"
    if "youtube.com" in parsed_url.netloc or "youtu.be" in parsed_url.netloc:
        return "youtube"
    if "arxiv.org" in parsed_url.netloc and "/abs/" in parsed_url.path:
        return "arxiv"
    if parsed_url.path.lower().endswith('.pdf'):
        return "pdf"
    return "web"


def _is_allowed_filetype(filename: str) -> bool:
    """Checks if a file extension is in the allowed list."""
    return Path(filename).suffix.lstrip('.').lower() in ALLOWED_EXTENSIONS


def _process_pdf_content(content: bytes) -> str:
    """Extracts text from PDF bytes."""
    try:
        with BytesIO(content) as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            return ' '.join(page.extract_text() or '' for page in pdf_reader.pages)
    except Exception as e:
        return f"Error processing PDF: {e}"


def process_github_repo(repo_url: str) -> Dict[str, Any]:
    """Processes a GitHub repository and returns structured file data."""
    repo_path = urlparse(repo_url).path.strip('/')
    parts = repo_path.split('/')
    repo_name = f"{parts[0]}/{parts[1]}"
    path_in_repo = ""
    branch = ""
    if len(parts) > 2 and parts[2] == "tree":
        branch = parts[3]
        path_in_repo = "/".join(parts[4:])

    api_url = f"https://api.github.com/repos/{repo_name}/contents/{path_in_repo}"
    if branch:
        api_url += f"?ref={branch}"

    files_data: List[Dict[str, str]] = []

    def fetch_dir_contents(url: str):
        try:
            response = requests.get(url, headers={'Accept': 'application/vnd.github.v3+json'})
            response.raise_for_status()
            for item in response.json():
                if item['type'] == 'dir' and item['name'] not in EXCLUDED_DIRS:
                    fetch_dir_contents(item['url'])
                elif item['type'] == 'file' and _is_allowed_filetype(item['name']):
                    file_resp = requests.get(item['download_url'])
                    if file_resp.status_code == 200:
                        files_data.append({'path': item['path'], 'content': file_resp.text})
        except requests.RequestException:
            pass  # Silently ignore directory fetch errors

    fetch_dir_contents(api_url)
    return {'files': files_data}


def process_youtube_transcript(url: str) -> Dict[str, Any]:
    """Fetches a YouTube transcript."""
    match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11}).*', url)
    video_id = match.group(1) if match else None
    if not video_id:
        return {'content': "Error: Could not extract YouTube video ID.", 'source': url}
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join(item["text"] for item in transcript_list)
        return {'content': transcript, 'source': url}
    except Exception as e:
        return {'content': f"Error fetching transcript: {e}", 'source': url}


def process_web_source(url: str) -> Dict[str, Any]:
    """Processes a generic web URL, ArXiv page, or direct PDF link."""
    source_url = url
    content = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        if get_url_type(url) == "arxiv":
            url = url.replace("/abs/", "/pdf/") + ".pdf"

        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()

        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            content = _process_pdf_content(response.content)
        elif 'text/html' in content_type:
            soup = BeautifulSoup(response.content, 'html.parser')
            for element in soup(['script', 'style', 'head', 'nav', 'footer', 'aside', 'form']):
                element.decompose()
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            content = soup.get_text(separator='\n', strip=True)
        else:
            content = f"Error: Unsupported content type '{content_type}'"

    except requests.RequestException as e:
        content = f"Error: Failed to fetch URL '{url}'. Reason: {e}"
    except Exception as e:
        content = f"Error: An unexpected error occurred. Reason: {e}"

    return {'content': content, 'source': source_url}