"""
Search Engine for DOI Citation Manager
Advanced search and filtering functionality
"""

import re
from datetime import datetime


class SearchEngine:
    """Advanced search and filtering engine"""

    def __init__(self, storage):
        self.storage = storage

    def search(self, query, filters=None, scope="all"):
        """
        Perform advanced search

        Args:
            query: Search query string
            filters: Dictionary of filter options
            scope: Search scope ('all', 'current_project', specific project_id)
        """
        # Get papers to search
        if scope == "all":
            papers = list(self.storage.data["papers"].values())
        elif scope == "current_project":
            # This would be set by the UI
            papers = []
        elif isinstance(scope, str):  # Assume it's a project_id
            papers = self.storage.get_papers_in_project(scope)
        else:
            papers = list(self.storage.data["papers"].values())

        # Apply text search
        if query:
            papers = self.text_search(papers, query)

        # Apply filters
        if filters:
            papers = self.apply_filters(papers, filters)

        return papers

    def text_search(self, papers, query):
        """Perform text search on papers"""
        if not query:
            return papers

        query_lower = query.lower()
        results = []

        for paper in papers:
            score = self.calculate_relevance_score(paper, query_lower)
            if score > 0:
                paper_with_score = paper.copy()
                paper_with_score["_search_score"] = score
                results.append(paper_with_score)

        # Sort by relevance score
        results.sort(key=lambda x: x.get("_search_score", 0), reverse=True)

        return results

    def calculate_relevance_score(self, paper, query):
        """Calculate relevance score for a paper"""
        score = 0

        # Search in title (highest weight)
        title = paper.get("title", "").lower()
        if query in title:
            score += 10
            # Bonus for exact word matches
            if self.contains_whole_word(title, query):
                score += 5

        # Search in authors (high weight)
        authors = paper.get("authors", [])
        author_text = self.format_authors_for_search(authors).lower()
        if query in author_text:
            score += 7

        # Search in abstract (medium weight)
        abstract = paper.get("abstract", "").lower()
        if query in abstract:
            score += 5

        # Search in journal name (medium weight)
        journal = self.get_journal_name(paper).lower()
        if query in journal:
            score += 4

        # Search in tags (medium weight)
        tags = paper.get("tags", [])
        tag_text = " ".join(tags).lower()
        if query in tag_text:
            score += 4

        # Search in notes (low weight)
        notes = paper.get("notes", "").lower()
        if query in notes:
            score += 2

        # Search in DOI (low weight)
        doi = paper.get("DOI", "").lower()
        if query in doi:
            score += 1

        return score

    def contains_whole_word(self, text, word):
        """Check if text contains word as a whole word"""
        pattern = r"\b" + re.escape(word) + r"\b"
        return bool(re.search(pattern, text, re.IGNORECASE))

    def format_authors_for_search(self, authors):
        """Format authors list for searching"""
        if not authors:
            return ""

        author_strings = []
        for author in authors:
            if isinstance(author, dict):
                parts = []
                if author.get("given"):
                    parts.append(author["given"])
                if author.get("family"):
                    parts.append(author["family"])
                if author.get("name"):
                    parts.append(author["name"])
                author_strings.append(" ".join(parts))
            else:
                author_strings.append(str(author))

        return " ".join(author_strings)

    def get_journal_name(self, paper):
        """Extract journal name from paper"""
        container_title = paper.get("container-title", [])
        if isinstance(container_title, list) and container_title:
            return container_title[0]
        elif isinstance(container_title, str):
            return container_title
        return ""

    def apply_filters(self, papers, filters):
        """Apply various filters to papers"""
        filtered_papers = papers.copy()

        # Year filter
        if filters.get("year_filter") and filters["year_filter"] != "all":
            year = filters["year_filter"]
            filtered_papers = [
                p for p in filtered_papers if self.get_paper_year(p) == year
            ]

        # Tag filter
        if filters.get("tag_filter") and filters["tag_filter"] != "all":
            tag = filters["tag_filter"]
            filtered_papers = [p for p in filtered_papers if tag in p.get("tags", [])]

        # Journal filter
        if filters.get("journal_filter") and filters["journal_filter"] != "all":
            journal = filters["journal_filter"]
            filtered_papers = [
                p for p in filtered_papers if self.get_journal_name(p) == journal
            ]

        # Type filter
        if filters.get("type_filter") and filters["type_filter"] != "all":
            paper_type = filters["type_filter"]
            filtered_papers = [
                p for p in filtered_papers if p.get("type") == paper_type
            ]

        # Date range filter
        if filters.get("date_from") or filters.get("date_to"):
            filtered_papers = self.filter_by_date_range(
                filtered_papers, filters.get("date_from"), filters.get("date_to")
            )

        # Has abstract filter
        if filters.get("has_abstract"):
            filtered_papers = [
                p for p in filtered_papers if p.get("abstract", "").strip()
            ]

        # Has notes filter
        if filters.get("has_notes"):
            filtered_papers = [p for p in filtered_papers if p.get("notes", "").strip()]

        return filtered_papers

    def get_paper_year(self, paper):
        """Extract publication year from paper"""
        # Try published-print first
        if "published-print" in paper:
            date_parts = paper["published-print"].get("date-parts", [[]])
            if date_parts and date_parts[0] and len(date_parts[0]) > 0:
                return date_parts[0][0]

        # Try published-online
        if "published-online" in paper:
            date_parts = paper["published-online"].get("date-parts", [[]])
            if date_parts and date_parts[0] and len(date_parts[0]) > 0:
                return date_parts[0][0]

        return None

    def filter_by_date_range(self, papers, date_from, date_to):
        """Filter papers by publication date range"""
        filtered_papers = []

        for paper in papers:
            year = self.get_paper_year(paper)
            if year:
                include = True

                if date_from and year < date_from:
                    include = False

                if date_to and year > date_to:
                    include = False

                if include:
                    filtered_papers.append(paper)

        return filtered_papers

    def get_search_suggestions(self, partial_query):
        """Get search suggestions based on partial query"""
        if len(partial_query) < 2:
            return []

        suggestions = set()
        papers = list(self.storage.data["papers"].values())

        # Search in titles
        for paper in papers:
            title = paper.get("title", "")
            words = title.lower().split()
            for word in words:
                if word.startswith(partial_query.lower()) and len(word) > 2:
                    suggestions.add(word)

        # Search in author names
        for paper in papers:
            authors = paper.get("authors", [])
            author_text = self.format_authors_for_search(authors)
            words = author_text.lower().split()
            for word in words:
                if word.startswith(partial_query.lower()) and len(word) > 2:
                    suggestions.add(word)

        # Search in tags
        for paper in papers:
            tags = paper.get("tags", [])
            for tag in tags:
                if tag.lower().startswith(partial_query.lower()):
                    suggestions.add(tag.lower())

        return sorted(list(suggestions))[:10]  # Return top 10

    def get_filter_options(self):
        """Get available filter options"""
        papers = list(self.storage.data["papers"].values())

        # Get unique years
        years = set()
        for paper in papers:
            year = self.get_paper_year(paper)
            if year:
                years.add(year)

        # Get unique journals
        journals = set()
        for paper in papers:
            journal = self.get_journal_name(paper)
            if journal:
                journals.add(journal)

        # Get unique types
        types = set()
        for paper in papers:
            paper_type = paper.get("type", "unknown")
            types.add(paper_type)

        # Get unique tags
        tags = set()
        for paper in papers:
            paper_tags = paper.get("tags", [])
            tags.update(paper_tags)

        return {
            "years": sorted(list(years), reverse=True),
            "journals": sorted(list(journals)),
            "types": sorted(list(types)),
            "tags": sorted(list(tags)),
        }
