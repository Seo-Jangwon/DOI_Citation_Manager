"""
Project Manager for DOI Citation Manager
Handles project-related operations and logic
"""

from datetime import datetime


class ProjectManager:
    """Manager for project operations"""

    def __init__(self, storage):
        self.storage = storage

    def create_project(self, name):
        """Create new project"""
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")

        # Check for duplicate names
        existing_projects = self.storage.get_all_projects()
        for project in existing_projects:
            if project["name"].lower() == name.strip().lower():
                raise ValueError(f"Project '{name}' already exists")

        return self.storage.create_project(name.strip())

    def get_all_projects(self):
        """Get all projects"""
        return self.storage.get_all_projects()

    def get_project_by_id(self, project_id):
        """Get project by ID"""
        return self.storage.get_project_by_id(project_id)

    def rename_project(self, project_id, new_name):
        """Rename project"""
        if not new_name or not new_name.strip():
            raise ValueError("Project name cannot be empty")

        # Check for duplicate names (excluding current project)
        existing_projects = self.storage.get_all_projects()
        for project in existing_projects:
            if (
                project["id"] != project_id
                and project["name"].lower() == new_name.strip().lower()
            ):
                raise ValueError(f"Project '{new_name}' already exists")

        return self.storage.rename_project(project_id, new_name.strip())

    def delete_project(self, project_id):
        """Delete project"""
        project = self.storage.get_project_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        return self.storage.delete_project(project_id)

    def get_papers_in_project(self, project_id):
        """Get all papers in project"""
        return self.storage.get_papers_in_project(project_id)

    def add_paper_to_project(self, project_id, paper_data):
        """Add paper to project"""
        project = self.storage.get_project_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        return self.storage.add_paper_to_project(project_id, paper_data)

    def remove_paper_from_project(self, project_id, paper_id):
        """Remove paper from project"""
        return self.storage.remove_paper_from_project(project_id, paper_id)

    def get_project_statistics(self, project_id):
        """Get statistics for project"""
        project = self.storage.get_project_by_id(project_id)
        if not project:
            return None

        papers = self.get_papers_in_project(project_id)

        # Count by year
        year_counts = {}
        for paper in papers:
            year = self.extract_year_from_paper(paper)
            if year:
                year_counts[year] = year_counts.get(year, 0) + 1

        # Count by journal
        journal_counts = {}
        for paper in papers:
            journal = self.extract_journal_from_paper(paper)
            if journal:
                journal_counts[journal] = journal_counts.get(journal, 0) + 1

        # Count by type
        type_counts = {}
        for paper in papers:
            paper_type = paper.get("type", "unknown")
            type_counts[paper_type] = type_counts.get(paper_type, 0) + 1

        return {
            "total_papers": len(papers),
            "years": year_counts,
            "journals": journal_counts,
            "types": type_counts,
            "created": project.get("created"),
            "modified": project.get("modified"),
        }

    def extract_year_from_paper(self, paper):
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

    def extract_journal_from_paper(self, paper):
        """Extract journal name from paper"""
        container_title = paper.get("container-title", [])
        if isinstance(container_title, list) and container_title:
            return container_title[0]
        elif isinstance(container_title, str):
            return container_title
        return None

    def duplicate_project(self, project_id, new_name=None):
        """Duplicate project with all its papers"""
        original_project = self.storage.get_project_by_id(project_id)
        if not original_project:
            raise ValueError("Project not found")

        # Generate new name if not provided
        if not new_name:
            new_name = f"{original_project['name']} (Copy)"

        # Create new project
        new_project = self.create_project(new_name)

        # Copy all papers to new project
        papers = self.get_papers_in_project(project_id)
        for paper in papers:
            self.storage.add_paper_to_project(new_project["id"], paper)

        return new_project

    def merge_projects(self, source_project_id, target_project_id):
        """Merge papers from source project into target project"""
        source_project = self.storage.get_project_by_id(source_project_id)
        target_project = self.storage.get_project_by_id(target_project_id)

        if not source_project or not target_project:
            raise ValueError("One or both projects not found")

        # Get papers from source project
        papers = self.get_papers_in_project(source_project_id)

        # Add papers to target project
        for paper in papers:
            self.storage.add_paper_to_project(target_project_id, paper)

        # Delete source project
        self.delete_project(source_project_id)

        return target_project

    def export_project(self, project_id, format_type="json"):
        """Export project data"""
        project = self.storage.get_project_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        papers = self.get_papers_in_project(project_id)

        export_data = {
            "project": project,
            "papers": papers,
            "exported": datetime.now().isoformat(),
            "format": format_type,
        }

        return export_data

    def import_project(self, project_data):
        """Import project from external data"""
        if not isinstance(project_data, dict):
            raise ValueError("Invalid project data format")

        if "project" not in project_data or "papers" not in project_data:
            raise ValueError("Missing required project data")

        project_info = project_data["project"]
        papers = project_data["papers"]

        # Create new project
        new_project = self.create_project(project_info["name"])

        # Add papers
        for paper in papers:
            self.storage.add_paper_to_project(new_project["id"], paper)

        return new_project

    def search_projects(self, query):
        """Search projects by name"""
        if not query:
            return self.get_all_projects()

        query = query.lower()
        results = []

        for project in self.get_all_projects():
            if query in project["name"].lower():
                results.append(project)

        return results
