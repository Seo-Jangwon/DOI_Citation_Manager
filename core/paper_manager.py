"""
Paper Manager for DOI Citation Manager
Handles paper-related operations and logic
"""

from datetime import datetime
import re


class PaperManager:
    """Manager for paper operations"""

    def __init__(self, storage):
        self.storage = storage

    def add_paper(self, paper_data):
        """Add paper to collection"""
        # Validate paper data
        if not isinstance(paper_data, dict):
            raise ValueError("Paper data must be a dictionary")

        # Ensure required fields
        if not paper_data.get("DOI") and not paper_data.get("title"):
            raise ValueError("Paper must have either DOI or title")

        return self.storage.add_paper(paper_data)

    def get_paper_by_id(self, paper_id):
        """Get paper by ID"""
        return self.storage.get_paper_by_id(paper_id)

    def update_paper(self, paper_id, updates):
        """Update paper data"""
        return self.storage.update_paper(paper_id, updates)

    def delete_paper(self, paper_id):
        """Delete paper completely"""
        return self.storage.delete_paper(paper_id)

    def add_paper_to_project(self, project_id, paper_data):
        """Add paper to specific project"""
        return self.storage.add_paper_to_project(project_id, paper_data)

    def remove_paper_from_project(self, project_id, paper_id):
        """Remove paper from project"""
        return self.storage.remove_paper_from_project(project_id, paper_id)

    def get_papers_in_project(self, project_id):
        """Get all papers in project"""
        return self.storage.get_papers_in_project(project_id)

    def search_papers(self, query, filters=None):
        """
        Search papers with advanced filtering

        Args:
            query: Search query string
            filters: Dictionary of filter options
        """
        if not query and not filters:
            return list(self.storage.data["papers"].values())

        # Start with basic search
        if query:
            results = self.storage.search_papers(query)
        else:
            results = list(self.storage.data["papers"].values())

        # Apply filters
        if filters:
            results = self.apply_filters(results, filters)

        return results

    def apply_filters(self, papers, filters):
        """Apply filters to paper list"""
        filtered_papers = papers.copy()

        # Filter by year
        if filters.get("year_filter") and filters["year_filter"] != "all":
            year = filters["year_filter"]
            filtered_papers = [
                p for p in filtered_papers if self.get_paper_year(p) == year
            ]

        # Filter by tag
        if filters.get("tag_filter") and filters["tag_filter"] != "all":
            tag = filters["tag_filter"]
            filtered_papers = [p for p in filtered_papers if tag in p.get("tags", [])]

        # Filter by journal
        if filters.get("journal_filter") and filters["journal_filter"] != "all":
            journal = filters["journal_filter"]
            filtered_papers = [
                p for p in filtered_papers if self.get_paper_journal(p) == journal
            ]

        # Filter by type
        if filters.get("type_filter") and filters["type_filter"] != "all":
            paper_type = filters["type_filter"]
            filtered_papers = [
                p for p in filtered_papers if p.get("type") == paper_type
            ]

        return filtered_papers

    def get_paper_year(self, paper):
        """Extract year from paper"""
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

    def get_paper_journal(self, paper):
        """Extract journal from paper"""
        container_title = paper.get("container-title", [])
        if isinstance(container_title, list) and container_title:
            return container_title[0]
        elif isinstance(container_title, str):
            return container_title
        return None

    def get_papers_by_tag(self, tag):
        """Get papers with specific tag"""
        return self.storage.get_papers_by_tag(tag)

    def add_tag_to_paper(self, paper_id, tag):
        """Add tag to paper"""
        paper = self.get_paper_by_id(paper_id)
        if not paper:
            raise ValueError("Paper not found")

        tags = paper.get("tags", [])
        if tag not in tags:
            tags.append(tag)
            self.update_paper(paper_id, {"tags": tags})

        return paper

    def remove_tag_from_paper(self, paper_id, tag):
        """Remove tag from paper"""
        paper = self.get_paper_by_id(paper_id)
        if not paper:
            raise ValueError("Paper not found")

        tags = paper.get("tags", [])
        if tag in tags:
            tags.remove(tag)
            self.update_paper(paper_id, {"tags": tags})

        return paper

    def update_paper_notes(self, paper_id, notes):
        """Update paper notes"""
        return self.update_paper(paper_id, {"notes": notes})

    def get_duplicate_papers(self):
        """Find potential duplicate papers"""
        papers = list(self.storage.data["papers"].values())
        duplicates = []

        for i, paper1 in enumerate(papers):
            for paper2 in papers[i + 1 :]:
                if self.are_papers_similar(paper1, paper2):
                    duplicates.append((paper1, paper2))

        return duplicates

    def are_papers_similar(self, paper1, paper2):
        """Check if two papers are similar (potential duplicates)"""
        # Compare DOIs
        doi1 = paper1.get("DOI", "").lower()
        doi2 = paper2.get("DOI", "").lower()
        if doi1 and doi2 and doi1 == doi2:
            return True

        # Compare titles (fuzzy match)
        title1 = paper1.get("title", "").lower()
        title2 = paper2.get("title", "").lower()
        if title1 and title2:
            # Simple similarity check
            title1_clean = re.sub(r"[^\w\s]", "", title1)
            title2_clean = re.sub(r"[^\w\s]", "", title2)

            # Check if one title contains most words of the other
            words1 = set(title1_clean.split())
            words2 = set(title2_clean.split())

            if len(words1) > 0 and len(words2) > 0:
                common_words = words1.intersection(words2)
                similarity = len(common_words) / min(len(words1), len(words2))
                if similarity > 0.8:  # 80% similar
                    return True

        return False

    def merge_duplicate_papers(self, paper1_id, paper2_id, keep_paper_id):
        """Merge two duplicate papers"""
        paper1 = self.get_paper_by_id(paper1_id)
        paper2 = self.get_paper_by_id(paper2_id)

        if not paper1 or not paper2:
            raise ValueError("One or both papers not found")

        if keep_paper_id not in [paper1_id, paper2_id]:
            raise ValueError("Keep paper ID must be one of the two papers")

        keep_paper = paper1 if keep_paper_id == paper1_id else paper2
        remove_paper = paper2 if keep_paper_id == paper1_id else paper1
        remove_paper_id = paper2_id if keep_paper_id == paper1_id else paper1_id

        # Merge tags
        keep_tags = set(keep_paper.get("tags", []))
        remove_tags = set(remove_paper.get("tags", []))
        merged_tags = list(keep_tags.union(remove_tags))

        # Merge notes
        keep_notes = keep_paper.get("notes", "")
        remove_notes = remove_paper.get("notes", "")
        merged_notes = keep_notes
        if remove_notes and remove_notes not in keep_notes:
            merged_notes = (
                f"{keep_notes}\n\n--- Merged from duplicate ---\n{remove_notes}"
            )

        # Update keep paper
        self.update_paper(
            keep_paper_id, {"tags": merged_tags, "notes": merged_notes.strip()}
        )

        # Delete remove paper
        self.delete_paper(remove_paper_id)

        return keep_paper

    def get_paper_statistics(self):
        """Get overall paper statistics"""
        papers = list(self.storage.data["papers"].values())

        # Count by year
        year_counts = {}
        for paper in papers:
            year = self.get_paper_year(paper)
            if year:
                year_counts[year] = year_counts.get(year, 0) + 1

        # Count by journal
        journal_counts = {}
        for paper in papers:
            journal = self.get_paper_journal(paper)
            if journal:
                journal_counts[journal] = journal_counts.get(journal, 0) + 1

        # Count by type
        type_counts = {}
        for paper in papers:
            paper_type = paper.get("type", "unknown")
            type_counts[paper_type] = type_counts.get(paper_type, 0) + 1

        # Most used tags
        tag_counts = {}
        for paper in papers:
            for tag in paper.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            "total_papers": len(papers),
            "years": year_counts,
            "journals": journal_counts,
            "types": type_counts,
            "tags": tag_counts,
            "papers_with_abstracts": len([p for p in papers if p.get("abstract")]),
            "papers_with_notes": len([p for p in papers if p.get("notes")]),
            "papers_with_tags": len([p for p in papers if p.get("tags")]),
        }

    def export_papers(self, paper_ids=None, format_type="json"):
        """Export papers to various formats"""
        if paper_ids:
            papers = [
                self.get_paper_by_id(pid)
                for pid in paper_ids
                if self.get_paper_by_id(pid)
            ]
        else:
            papers = list(self.storage.data["papers"].values())

        export_data = {
            "papers": papers,
            "exported": datetime.now().isoformat(),
            "format": format_type,
            "count": len(papers),
        }

        return export_data

    def import_papers(self, papers_data):
        """Import papers from external data"""
        if not isinstance(papers_data, list):
            raise ValueError("Papers data must be a list")

        imported_papers = []
        for paper_data in papers_data:
            try:
                paper = self.add_paper(paper_data)
                imported_papers.append(paper)
            except Exception as e:
                print(f"Error importing paper: {e}")
                continue

        return imported_papers

    def validate_paper_data(self, paper_data):
        """Validate paper data structure"""
        required_fields = ["title"]
        recommended_fields = ["authors", "DOI", "container-title"]

        errors = []
        warnings = []

        # Check required fields
        for field in required_fields:
            if not paper_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Check recommended fields
        for field in recommended_fields:
            if not paper_data.get(field):
                warnings.append(f"Missing recommended field: {field}")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
