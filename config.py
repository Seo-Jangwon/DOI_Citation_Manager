"""
Configuration constants for DOI Citation Manager
- 사용자 데이터를 AppData/Roaming에 저장
- 크로스 플랫폼 지원
"""

import os
import sys
from pathlib import Path

# Application info
APP_NAME = "DOI Citation Manager"
APP_FOLDER_NAME = "DOICitationManager"  # 폴더명
VERSION = "1.0.0"
AUTHOR = "DOI Tools"


# 사용자 데이터 디렉토리 결정 (크로스 플랫폼)
def get_user_data_dir():
    """사용자 데이터 디렉토리 경로를 반환"""
    if sys.platform == "win32":
        # Windows: %APPDATA%\DOICitationManager
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_FOLDER_NAME
        else:
            # fallback
            return Path.home() / "AppData" / "Roaming" / APP_FOLDER_NAME
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/DOICitationManager
        return Path.home() / "Library" / "Application Support" / APP_FOLDER_NAME
    else:
        # Linux: ~/.local/share/DOICitationManager
        return Path.home() / ".local" / "share" / APP_FOLDER_NAME


# 현재 실행 파일의 디렉토리 (리소스용)
if getattr(sys, "frozen", False):
    # PyInstaller로 패키징된 경우
    APP_DIR = Path(sys.executable).parent
else:
    # 개발 환경
    APP_DIR = Path(__file__).parent

# 사용자 데이터 디렉토리
USER_DATA_DIR = get_user_data_dir()
DATA_DIR = USER_DATA_DIR / "data"
BACKUP_DIR = USER_DATA_DIR / "backups"
CACHE_DIR = USER_DATA_DIR / "cache"

# 리소스 디렉토리 (실행파일과 함께 배포)
RESOURCES_DIR = APP_DIR / "resources"

# 필요한 디렉토리 생성
for directory in [USER_DATA_DIR, DATA_DIR, BACKUP_DIR, CACHE_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create directory {directory}: {e}")

# 리소스 디렉토리도 생성 (개발 환경에서)
if not getattr(sys, "frozen", False):
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

# Files
DATABASE_FILE = DATA_DIR / "projects.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
CACHE_FILE = CACHE_DIR / "citations_cache.json"
LOG_FILE = USER_DATA_DIR / "app.log"

# DOI API settings
DOI_API_BASE = "https://doi.org/"
CROSSREF_API_BASE = "https://api.crossref.org/works/"
REQUEST_TIMEOUT = 15
USER_AGENT = f"{APP_NAME}/{VERSION} (https://github.com/user/doi-manager)"

# UI settings
DEFAULT_THEME = "light"
WINDOW_SIZE = (1400, 900)
MIN_WINDOW_SIZE = (1000, 600)

# Citation formats supported (확장된 목록)
CITATION_FORMATS = {
    "APA": {
        "accept_header": "text/x-bibliography; style=apa; locale=en-US",
        "display_name": "APA Style",
    },
    "IEEE": {
        "accept_header": "text/x-bibliography; style=ieee; locale=en-US",
        "display_name": "IEEE Style",
    },
    "Nature": {
        "accept_header": "text/x-bibliography; style=nature; locale=en-US",
        "display_name": "Nature Style",
    },
    "Science": {
        "accept_header": "text/x-bibliography; style=science; locale=en-US",
        "display_name": "Science Style",
    },
    "Cell": {
        "accept_header": "text/x-bibliography; style=cell; locale=en-US",
        "display_name": "Cell Style",
    },
    "PNAS": {
        "accept_header": "text/x-bibliography; style=pnas; locale=en-US",
        "display_name": "PNAS Style",
    },
    "PLoS": {
        "accept_header": "text/x-bibliography; style=plos; locale=en-US",
        "display_name": "PLoS Style",
    },
    "MLA": {
        "accept_header": "text/x-bibliography; style=modern-language-association; locale=en-US",
        "display_name": "MLA Style",
    },
    "Chicago": {
        "accept_header": "text/x-bibliography; style=chicago-author-date; locale=en-US",
        "display_name": "Chicago Style",
    },
    "Harvard": {
        "accept_header": "text/x-bibliography; style=harvard-cite-them-right; locale=en-US",
        "display_name": "Harvard Style",
    },
    "Vancouver": {
        "accept_header": "text/x-bibliography; style=vancouver; locale=en-US",
        "display_name": "Vancouver Style",
    },
    "BibTeX": {"accept_header": "application/x-bibtex", "display_name": "BibTeX"},
    "RIS": {
        "accept_header": "application/x-research-info-systems",
        "display_name": "RIS (EndNote/Mendeley)",
    },
    "JSON": {
        "accept_header": "application/vnd.citationstyles.csl+json",
        "display_name": "CSL-JSON",
    },
}

# Default citation format
DEFAULT_CITATION_FORMAT = "APA"

# DOI regex pattern
DOI_PATTERN = r"10\.\d{4,}\/[^\s\]>,;]+"

# Theme files
THEMES = {
    "light": RESOURCES_DIR / "styles" / "light_theme.qss",
    "dark": RESOURCES_DIR / "styles" / "dark_theme.qss",
}

# Default project structure
DEFAULT_PROJECTS = [
    "Research Papers",
    "Literature Review",
    "Methodology",
    "Related Work",
]

# Keyboard shortcuts
SHORTCUTS = {
    "convert_doi": "Ctrl+Return",
    "new_project": "Ctrl+N",
    "search": "Ctrl+F",
    "copy_citation": "Ctrl+C",
    "paste_doi": "Ctrl+V",
    "paste_and_convert": "Ctrl+Shift+V",
    "save": "Ctrl+S",
    "export": "Ctrl+E",
    "import": "Ctrl+I",
    "toggle_theme": "Ctrl+T",
    "batch_convert": "Ctrl+B",
    "focus_search": "Ctrl+Shift+F",
    "new_paper": "Ctrl+Shift+N",
    "delete_item": "Delete",
    "refresh": "F5",
    "help": "F1",
}

# Export formats
EXPORT_FORMATS = {
    "JSON": {"extension": ".json", "filter": "JSON files (*.json)"},
    "BibTeX": {"extension": ".bib", "filter": "BibTeX files (*.bib)"},
    "RIS": {"extension": ".ris", "filter": "RIS files (*.ris)"},
    "CSV": {"extension": ".csv", "filter": "CSV files (*.csv)"},
    "XML": {"extension": ".xml", "filter": "XML files (*.xml)"},
    "TXT": {"extension": ".txt", "filter": "Text files (*.txt)"},
}

# UI Colors
COLORS = {
    "primary": "#2196F3",
    "secondary": "#FFC107",
    "success": "#4CAF50",
    "error": "#F44336",
    "warning": "#FF9800",
    "info": "#00BCD4",
    "accent": "#9C27B0",
}

# Paper metadata fields
PAPER_FIELDS = [
    "title",
    "authors",
    "journal",
    "year",
    "volume",
    "issue",
    "pages",
    "doi",
    "abstract",
    "url",
    "tags",
    "notes",
    "citations",
    "publisher",
    "type",
    "subject",
    "ISSN",
    "ISBN",
]

# Performance limits
MAX_RECENT_DOIS = 50
MAX_SEARCH_RESULTS = 100
MAX_BACKUP_FILES = 10

# Application settings
APP_SETTINGS = {
    "auto_backup": True,
    "backup_interval_days": 7,
    "max_backup_files": MAX_BACKUP_FILES,
    "cache_enabled": True,
    "cache_expiry_days": 30,
    "check_updates": True,
    "send_analytics": False,
}

# DOI input validation settings
DOI_INPUT_SETTINGS = {
    "auto_clean": True,
    "support_urls": True,
    "support_sci_hub": True,
    "extract_from_text": True,
    "validate_realtime": True,
}

# Citation generation settings
CITATION_SETTINGS = {
    "generate_all_formats": True,
    "parallel_generation": False,
    "cache_citations": True,
    "retry_failed": True,
    "max_retries": 3,
}

# Search settings
SEARCH_SETTINGS = {
    "fuzzy_search": True,
    "search_delay_ms": 500,
    "max_results": MAX_SEARCH_RESULTS,
    "highlight_matches": True,
}

# Network settings
NETWORK_SETTINGS = {
    "timeout": REQUEST_TIMEOUT,
    "max_connections": 5,
    "retry_attempts": 3,
    "use_cache": True,
}

# Logging settings
LOGGING_SETTINGS = {
    "level": "INFO",
    "max_file_size_mb": 10,
    "backup_count": 3,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}


def get_app_info():
    """애플리케이션 정보 반환"""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "author": AUTHOR,
        "data_dir": str(USER_DATA_DIR),
        "config_file": str(SETTINGS_FILE),
        "database_file": str(DATABASE_FILE),
    }


def print_paths():
    """디버깅용: 모든 경로 출력"""
    print(f"App Directory: {APP_DIR}")
    print(f"User Data Directory: {USER_DATA_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Backup Directory: {BACKUP_DIR}")
    print(f"Cache Directory: {CACHE_DIR}")
    print(f"Resources Directory: {RESOURCES_DIR}")
    print(f"Database File: {DATABASE_FILE}")
    print(f"Settings File: {SETTINGS_FILE}")


if __name__ == "__main__":
    print_paths()
