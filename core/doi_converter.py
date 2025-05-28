"""
DOI Converter - Core logic for DOI to citation conversion
- 모든 인용 형식을 자동으로 생성
- 향상된 오류 처리
"""

import requests
import json
import re
import html
from datetime import datetime
from config import (
    DOI_API_BASE,
    CROSSREF_API_BASE,
    CITATION_FORMATS,
    REQUEST_TIMEOUT,
    USER_AGENT,
    DOI_PATTERN,
)


class DOIConverter:
    """Main class for converting DOIs to various citation formats"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def convert_doi(self, doi):
        """
        Convert DOI to all citation formats

        Args:
            doi: DOI string (e.g., "10.1038/nature12373")

        Returns:
            dict: Paper data with metadata and all citation formats
        """
        # Clean DOI
        doi = self.clean_doi(doi)

        # Get basic metadata first
        metadata = self.get_doi_metadata(doi)

        # Generate citations in ALL formats automatically
        citations = {}
        for fmt_key, fmt_info in CITATION_FORMATS.items():
            try:
                citation = self.get_formatted_citation(doi, fmt_key)
                citations[fmt_key] = citation
            except Exception as e:
                print(f"Warning: Failed to get {fmt_key} citation: {e}")
                citations[fmt_key] = f"Error: {str(e)}"

        # Combine metadata and citations
        paper_data = {
            **metadata,
            "citations": citations,
            "added_date": datetime.now().isoformat(),
            "tags": [],
            "notes": "",
        }

        return paper_data

    def clean_doi(self, doi):
        """Clean and validate DOI string"""
        if not doi:
            raise ValueError("DOI cannot be empty")

        # Remove common prefixes (확장된 목록)
        doi = doi.strip()
        prefixes = [
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "https://www.doi.org/",
            "http://www.doi.org/",
            "doi.org/",
            "dx.doi.org/",
            "www.doi.org/",
            "doi:",
            "DOI:",
            "doi ",
            "DOI ",
        ]

        for prefix in prefixes:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix) :]
                break

        # Remove URL parameters and anchors
        if "?" in doi:
            doi = doi.split("?")[0]
        if "#" in doi:
            doi = doi.split("#")[0]

        # Remove trailing slash
        doi = doi.rstrip("/")

        # Validate DOI format
        if not re.match(DOI_PATTERN, doi):
            raise ValueError(f"Invalid DOI format: {doi}")

        return doi

    def get_doi_metadata(self, doi):
        """Get basic metadata for DOI using CrossRef API"""
        try:
            # Try CrossRef REST API first
            url = f"{CROSSREF_API_BASE}{doi}"
            headers = {"Accept": "application/json"}

            response = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()
            work = data["message"]

            # Extract and normalize metadata
            metadata = self.normalize_crossref_metadata(work)
            return metadata

        except requests.exceptions.RequestException as e:
            # Fallback to DOI content negotiation
            return self.get_doi_metadata_fallback(doi)

    def normalize_crossref_metadata(self, work):
        """Normalize CrossRef metadata to standard format"""
        # Extract title
        title = ""
        if "title" in work and work["title"]:
            title = (
                work["title"][0] if isinstance(work["title"], list) else work["title"]
            )

        # Extract authors
        authors = []
        if "author" in work:
            for author in work["author"]:
                author_info = {}
                if "given" in author:
                    author_info["given"] = author["given"]
                if "family" in author:
                    author_info["family"] = author["family"]
                if "name" in author:
                    author_info["name"] = author["name"]
                authors.append(author_info)

        # Extract journal/container
        container_title = ""
        if "container-title" in work and work["container-title"]:
            container_title = (
                work["container-title"][0]
                if isinstance(work["container-title"], list)
                else work["container-title"]
            )

        # Extract publication date
        published_date = None
        if "published-print" in work:
            date_parts = work["published-print"].get("date-parts", [[]])
            if date_parts and date_parts[0]:
                published_date = date_parts[0]
        elif "published-online" in work:
            date_parts = work["published-online"].get("date-parts", [[]])
            if date_parts and date_parts[0]:
                published_date = date_parts[0]

        # Extract other fields
        volume = work.get("volume", "")
        issue = work.get("issue", "")
        pages = work.get("page", "")
        doi = work.get("DOI", "")

        # Clean abstract - remove HTML/XML tags
        abstract = work.get("abstract", "")
        if abstract:
            abstract = self.clean_abstract(abstract)

        url = work.get("URL", "")
        publisher = work.get("publisher", "")
        work_type = work.get("type", "journal-article")

        return {
            "id": doi,  # Use DOI as ID
            "title": title,
            "authors": authors,
            "container-title": [container_title] if container_title else [],
            "publisher": publisher,
            "published-print": (
                {"date-parts": [published_date]} if published_date else {}
            ),
            "published-online": work.get("published-online", {}),
            "volume": volume,
            "issue": issue,
            "page": pages,
            "DOI": doi,
            "URL": url,
            "abstract": abstract,
            "type": work_type,
            "subject": work.get("subject", []),
            "ISSN": work.get("ISSN", []),
            "ISBN": work.get("ISBN", []),
        }

    def clean_abstract(self, abstract):
        """Clean abstract by removing HTML/XML tags and fixing encoding"""
        if not abstract:
            return ""

        # Remove JATS XML tags
        abstract = re.sub(r"<jats:[^>]*>", "", abstract)
        abstract = re.sub(r"</jats:[^>]*>", "", abstract)

        # Remove other HTML tags
        abstract = re.sub(r"<[^>]+>", "", abstract)

        # Fix HTML entities
        abstract = html.unescape(abstract)

        # Clean up whitespace
        abstract = re.sub(r"\s+", " ", abstract).strip()

        return abstract

    def get_doi_metadata_fallback(self, doi):
        """Fallback method to get DOI metadata"""
        try:
            url = f"{DOI_API_BASE}{doi}"
            headers = {"Accept": "application/vnd.citationstyles.csl+json"}

            response = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Check if response is JSON
            content_type = response.headers.get("content-type", "")
            if (
                "application/json" not in content_type
                and "application/vnd.citationstyles.csl+json" not in content_type
            ):
                raise Exception("DOI resolver did not return expected JSON format")

            data = response.json()

            # Clean abstract in fallback data too
            abstract = data.get("abstract", "")
            if abstract:
                abstract = self.clean_abstract(abstract)

            # Normalize the data (CSL-JSON format is already close to our format)
            return {
                "id": data.get("DOI", doi),
                "title": data.get("title", "Unknown Title"),
                "authors": data.get("author", []),
                "container-title": data.get("container-title", []),
                "publisher": data.get("publisher", ""),
                "published-print": data.get("published-print", {}),
                "published-online": data.get("published-online", {}),
                "volume": data.get("volume", ""),
                "issue": data.get("issue", ""),
                "page": data.get("page", ""),
                "DOI": data.get("DOI", doi),
                "URL": data.get("URL", ""),
                "abstract": abstract,
                "type": data.get("type", "journal-article"),
                "subject": data.get("subject", []),
                "ISSN": data.get("ISSN", []),
                "ISBN": data.get("ISBN", []),
            }

        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Please check your internet connection.")
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Could not connect to DOI service. Please check your internet connection."
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception("DOI not found. Please verify the DOI is correct.")
            else:
                raise Exception(f"DOI service returned error: {e.response.status_code}")
        except Exception as e:
            if "JSON" in str(e):
                raise Exception("DOI service returned invalid data format.")
            raise Exception(f"Failed to retrieve metadata for DOI {doi}: {str(e)}")

    def get_formatted_citation(self, doi, format_key):
        """Get formatted citation for specific format"""
        if format_key not in CITATION_FORMATS:
            raise ValueError(f"Unsupported citation format: {format_key}")

        format_info = CITATION_FORMATS[format_key]
        accept_header = format_info["accept_header"]

        try:
            url = f"{DOI_API_BASE}{doi}"
            headers = {"Accept": accept_header}

            response = self.session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Return the formatted citation
            citation = response.text.strip()

            # Clean up common issues
            citation = self.clean_citation(citation, format_key)

            return citation

        except requests.exceptions.RequestException as e:
            # 더 구체적인 오류 메시지
            if hasattr(e, "response") and e.response is not None:
                if e.response.status_code == 406:
                    return f"Format {format_key} not supported by publisher"
                elif e.response.status_code == 404:
                    return "DOI not found"
                else:
                    return f"Service error (HTTP {e.response.status_code})"
            else:
                return f"Connection error: {str(e)}"

    def clean_citation(self, citation, format_key):
        """Clean up citation text"""
        if not citation:
            return "Citation not available"

        # Fix encoding issues
        citation = html.unescape(citation)

        # Fix common character encoding problems
        citation = citation.replace("â", '"')
        citation = citation.replace("â", '"')
        citation = citation.replace("â", "—")
        citation = citation.replace("Â", " ")

        # Remove excessive whitespace
        citation = re.sub(r"\s+", " ", citation).strip()

        # Format-specific cleaning
        if format_key == "BibTeX":
            # Ensure BibTeX is properly formatted
            if not citation.startswith("@"):
                return "Invalid BibTeX format"

        elif format_key == "RIS":
            # Ensure RIS is properly formatted
            if not citation.startswith("TY  -"):
                return "Invalid RIS format"

        return citation

    def batch_convert(self, doi_list):
        """
        Convert multiple DOIs to citations

        Args:
            doi_list: List of DOI strings

        Returns:
            list: List of paper data dictionaries
        """
        results = []

        for doi in doi_list:
            try:
                paper_data = self.convert_doi(doi)
                results.append(paper_data)
            except Exception as e:
                # Add error entry with more details
                results.append(
                    {
                        "id": doi,
                        "title": f"Error: {str(e)}",
                        "authors": [],
                        "DOI": doi,
                        "citations": {},
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )

        return results

    def validate_doi(self, doi):
        """Validate DOI format and accessibility"""
        try:
            cleaned_doi = self.clean_doi(doi)

            # Try to get metadata
            metadata = self.get_doi_metadata(cleaned_doi)
            return True, "Valid DOI"

        except Exception as e:
            return False, str(e)

    def get_citation_preview(self, doi, format_key):
        """Get a quick citation preview without full metadata"""
        try:
            citation = self.get_formatted_citation(doi, format_key)
            return citation
        except Exception as e:
            return f"Preview not available: {str(e)}"

    def get_available_formats(self):
        """Get list of available citation formats"""
        return list(CITATION_FORMATS.keys())

    def is_format_supported(self, format_key):
        """Check if citation format is supported"""
        return format_key in CITATION_FORMATS
