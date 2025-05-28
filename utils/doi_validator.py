"""
DOI Validator for DOI Citation Manager
- 더 유연한 DOI 입력 처리
- URL에서 DOI 추출 기능 강화
- sci-hub 스타일 입력 지원
"""

import re
import requests
from urllib.parse import urlparse, unquote
from config import DOI_PATTERN, DOI_API_BASE, REQUEST_TIMEOUT


class DOIValidator:
    """Validator for DOI format and accessibility"""

    def __init__(self):
        self.doi_pattern = re.compile(DOI_PATTERN)

        # 확장된 DOI 패턴들
        self.doi_patterns = [
            # 기본 DOI 패턴
            r"10\.\d{4,}/[^\s\]>,;]+",
            # URL 내 DOI 패턴
            r"(?:doi\.org/|dx\.doi\.org/)?(10\.\d{4,}/[^\s\]>,;/?]+)",
            # HTML 내 DOI 패턴
            r'doi[:\s]*["\']?(10\.\d{4,}/[^\s\]>,;"\']+)["\']?',
        ]

    def extract_doi_from_input(self, input_text):
        """
        다양한 입력 형식에서 DOI 추출 (새로운 기능)
        지원 형식:
        - 순수 DOI: 10.1038/nature12373
        - DOI URL: https://doi.org/10.1038/nature12373
        - 논문 URL: https://www.nature.com/articles/nature12373
        - DOI 접두사: doi:10.1038/nature12373
        - sci-hub 스타일: sci-hub.tw/10.1038/nature12373
        """
        if not input_text:
            return None

        input_text = input_text.strip()

        # 1. 기본 DOI 형식 확인
        basic_doi = self.clean_doi(input_text)
        if self.is_valid_doi_format(basic_doi):
            return basic_doi

        # 2. URL에서 DOI 추출 시도
        doi_from_url = self.extract_doi_from_url(input_text)
        if doi_from_url:
            return doi_from_url

        # 3. 텍스트에서 DOI 패턴 검색
        extracted_dois = self.extract_dois_from_text(input_text)
        if extracted_dois:
            return extracted_dois[0]  # 첫 번째 발견된 DOI 반환

        return None

    def extract_doi_from_url(self, url):
        """URL에서 DOI 추출 (새로운 기능)"""
        if not url:
            return None

        # URL 디코딩
        url = unquote(url)

        # 일반적인 DOI URL 패턴들
        doi_url_patterns = [
            # https://doi.org/10.1038/nature12373
            r"(?:https?://)?(?:dx\.)?doi\.org/(.+)",
            # https://www.nature.com/articles/nature12373 -> 10.1038/nature12373
            r"(?:https?://)?www\.nature\.com/articles/([^/?]+)",
            # https://science.sciencemag.org/content/early/2021/12/16/science.abm7892
            r"(?:https?://)?science\.sciencemag\.org/content/[^/]+/[^/]+/[^/]+/science\.([^/?]+)",
            # https://www.cell.com/cell/fulltext/S0092-8674(21)01496-3
            r"(?:https?://)?www\.cell\.com/[^/]+/fulltext/S\d+-\d+\(\d+\)\d+-\d+",
            # https://www.pnas.org/content/118/52/e2117553118
            r"(?:https?://)?www\.pnas\.org/content/\d+/\d+/e(\d+)",
            # sci-hub URLs
            r"(?:https?://)?(?:sci-hub\.[^/]+/)?(.+)",
        ]

        for pattern in doi_url_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                potential_doi = match.group(1)

                # Nature 특별 처리
                if "nature.com" in url and potential_doi:
                    potential_doi = f"10.1038/{potential_doi}"

                # Science 특별 처리
                elif "sciencemag.org" in url and potential_doi:
                    potential_doi = f"10.1126/science.{potential_doi}"

                # PNAS 특별 처리
                elif "pnas.org" in url and potential_doi:
                    potential_doi = f"10.1073/pnas.{potential_doi}"

                # Cell 특별 처리 (복잡한 URL 구조)
                elif "cell.com" in url:
                    # Cell URL에서 DOI 추출은 더 복잡하므로 기본 검색으로 넘김
                    continue

                # 추출된 DOI 검증
                cleaned_doi = self.clean_doi(potential_doi)
                if self.is_valid_doi_format(cleaned_doi):
                    return cleaned_doi

        return None

    def clean_doi(self, doi):
        """Clean DOI string by removing common prefixes"""
        if not doi:
            return ""

        doi = doi.strip()

        # 확장된 접두사 목록
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
            "doi=",
            "DOI=",
        ]

        # 접두사 제거
        for prefix in prefixes:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix) :]
                break

        # URL 매개변수 제거 (? 이후)
        if "?" in doi:
            doi = doi.split("?")[0]

        # 앵커 제거 (# 이후)
        if "#" in doi:
            doi = doi.split("#")[0]

        # 후행 슬래시 제거
        doi = doi.rstrip("/")

        return doi.strip()

    def is_valid_doi_format(self, doi):
        """Check if DOI has valid format"""
        if not doi:
            return False

        # Clean the DOI
        cleaned_doi = self.clean_doi(doi)

        # Check format with regex
        return bool(self.doi_pattern.match(cleaned_doi))

    def is_valid_doi(self, doi):
        """Check if DOI is valid (format + accessible)"""
        # First check format
        if not self.is_valid_doi_format(doi):
            return False

        # Then check if it's accessible (optional - can be slow)
        # For now, just return format validation
        # In production, you might want to make this configurable
        return True

    def check_doi_accessibility(self, doi):
        """Check if DOI is accessible online"""
        try:
            cleaned_doi = self.clean_doi(doi)
            url = f"{DOI_API_BASE}{cleaned_doi}"

            # Make a HEAD request to check accessibility without downloading content
            response = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)

            # Consider it accessible if we get a valid HTTP response
            return 200 <= response.status_code < 400

        except requests.RequestException:
            return False

    def validate_doi_batch(self, doi_list):
        """Validate a list of DOIs"""
        results = []

        for doi in doi_list:
            result = {
                "doi": doi,
                "cleaned_doi": self.clean_doi(doi),
                "valid_format": self.is_valid_doi_format(doi),
                "accessible": None,  # Will be filled if checked
            }
            results.append(result)

        return results

    def extract_dois_from_text(self, text):
        """Extract all DOIs from a text string"""
        if not text:
            return []

        # Find all DOI patterns in text
        dois = []

        # 확장된 패턴들로 검색
        for pattern in self.doi_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # 매치된 그룹에서 DOI 추출
                if match.groups():
                    doi = match.group(1) if len(match.groups()) > 0 else match.group(0)
                else:
                    doi = match.group(0)

                cleaned_doi = self.clean_doi(doi)
                if cleaned_doi and self.is_valid_doi_format(cleaned_doi):
                    dois.append(cleaned_doi)

        # Remove duplicates while preserving order
        unique_dois = []
        seen = set()
        for doi in dois:
            if doi not in seen:
                unique_dois.append(doi)
                seen.add(doi)

        return unique_dois

    def suggest_doi_corrections(self, invalid_doi):
        """Suggest corrections for invalid DOI"""
        suggestions = []

        if not invalid_doi:
            return suggestions

        original = invalid_doi.strip()

        # Common mistakes and corrections
        corrections = [
            # Missing prefix
            (r"^(\d+\.\d+/.+)$", r"10.\1"),
            # Wrong separators
            (r"10[._](\d+)[._](.+)", r"10.\1/\2"),
            # Extra spaces
            (r"10\.\s*(\d+)\s*/\s*(.+)", r"10.\1/\2"),
            # Wrong case
            (r"(?i)^doi:?\s*(.+)", r"\1"),
            # URL fragments
            (r".*/10\.(\d+/.+)", r"10.\1"),
        ]

        for pattern, replacement in corrections:
            corrected = re.sub(pattern, replacement, original)
            if corrected != original and self.is_valid_doi_format(corrected):
                suggestions.append(corrected)

        return suggestions

    def get_doi_parts(self, doi):
        """Parse DOI into its components"""
        cleaned_doi = self.clean_doi(doi)

        if not self.is_valid_doi_format(cleaned_doi):
            return None

        # Split into prefix and suffix
        parts = cleaned_doi.split("/", 1)
        if len(parts) != 2:
            return None

        prefix = parts[0]
        suffix = parts[1]

        # Further parse prefix
        prefix_parts = prefix.split(".")
        if len(prefix_parts) < 2:
            return None

        return {
            "full_doi": cleaned_doi,
            "prefix": prefix,
            "suffix": suffix,
            "directory_indicator": prefix_parts[0],  # Usually '10'
            "registrant_code": ".".join(prefix_parts[1:]),
        }

    def format_doi_for_display(self, doi):
        """Format DOI for consistent display"""
        cleaned_doi = self.clean_doi(doi)

        if not self.is_valid_doi_format(cleaned_doi):
            return doi  # Return original if invalid

        return cleaned_doi

    def format_doi_as_url(self, doi):
        """Format DOI as clickable URL"""
        cleaned_doi = self.clean_doi(doi)

        if not self.is_valid_doi_format(cleaned_doi):
            return None

        return f"{DOI_API_BASE}{cleaned_doi}"

    def validate_doi_comprehensive(self, doi):
        """Comprehensive DOI validation with detailed results"""
        result = {
            "original_doi": doi,
            "cleaned_doi": self.clean_doi(doi),
            "valid_format": False,
            "accessible": None,
            "errors": [],
            "warnings": [],
            "suggestions": [],
        }

        if not doi:
            result["errors"].append("DOI is empty")
            return result

        # Check format
        if not self.is_valid_doi_format(doi):
            result["errors"].append("Invalid DOI format")
            result["suggestions"] = self.suggest_doi_corrections(doi)
        else:
            result["valid_format"] = True

        # Check for common issues
        if "/" not in result["cleaned_doi"]:
            result["warnings"].append("DOI should contain a forward slash")

        if not result["cleaned_doi"].startswith("10."):
            result["warnings"].append("DOI should start with '10.'")

        # Check accessibility (optional)
        if result["valid_format"]:
            try:
                result["accessible"] = self.check_doi_accessibility(
                    result["cleaned_doi"]
                )
                if not result["accessible"]:
                    result["warnings"].append("DOI may not be accessible online")
            except Exception:
                result["warnings"].append("Could not check DOI accessibility")

        return result

    def is_likely_doi_url(self, url):
        """Check if URL likely contains a DOI (새로운 기능)"""
        if not url:
            return False

        # DOI 관련 도메인들
        doi_domains = [
            "doi.org",
            "dx.doi.org",
            "nature.com",
            "sciencemag.org",
            "cell.com",
            "pnas.org",
            "science.org",
            "springer.com",
            "wiley.com",
            "elsevier.com",
            "ieee.org",
            "acm.org",
            "sci-hub",
        ]

        url_lower = url.lower()
        return any(domain in url_lower for domain in doi_domains)
