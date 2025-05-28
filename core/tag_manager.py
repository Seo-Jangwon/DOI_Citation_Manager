"""
Tag Manager for DOI Citation Manager
Handles tag-related operations and logic
"""


class TagManager:
    """Manager for tag operations"""

    def __init__(self, storage):
        self.storage = storage

    def get_all_tags(self):
        """Get all unique tags from all papers"""
        return self.storage.get_all_tags()

    def get_tag_usage_count(self):
        """Get usage count for each tag"""
        tag_counts = {}
        papers = list(self.storage.data["papers"].values())

        for paper in papers:
            tags = paper.get("tags", [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return tag_counts

    def get_popular_tags(self, limit=10):
        """Get most popular tags"""
        tag_counts = self.get_tag_usage_count()
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, count in sorted_tags[:limit]]

    def get_papers_by_tag(self, tag):
        """Get all papers with specific tag"""
        return self.storage.get_papers_by_tag(tag)

    def add_tag_to_paper(self, paper_id, tag):
        """Add tag to paper"""
        paper = self.storage.get_paper_by_id(paper_id)
        if not paper:
            raise ValueError("Paper not found")

        # Normalize tag
        normalized_tag = self.normalize_tag(tag)
        if not normalized_tag:
            raise ValueError("Invalid tag")

        # Add tag if not already present
        tags = paper.get("tags", [])
        if normalized_tag not in tags:
            tags.append(normalized_tag)
            self.storage.update_paper(paper_id, {"tags": tags})

        return paper

    def remove_tag_from_paper(self, paper_id, tag):
        """Remove tag from paper"""
        paper = self.storage.get_paper_by_id(paper_id)
        if not paper:
            raise ValueError("Paper not found")

        tags = paper.get("tags", [])
        if tag in tags:
            tags.remove(tag)
            self.storage.update_paper(paper_id, {"tags": tags})

        return paper

    def rename_tag(self, old_tag, new_tag):
        """Rename tag across all papers"""
        if not old_tag or not new_tag:
            raise ValueError("Tag names cannot be empty")

        normalized_new_tag = self.normalize_tag(new_tag)
        if not normalized_new_tag:
            raise ValueError("Invalid new tag name")

        if old_tag == normalized_new_tag:
            return  # No change needed

        # Update all papers with this tag
        papers = list(self.storage.data["papers"].values())
        updated_count = 0

        for paper in papers:
            tags = paper.get("tags", [])
            if old_tag in tags:
                # Replace old tag with new tag
                tags = [normalized_new_tag if t == old_tag else t for t in tags]
                # Remove duplicates
                tags = list(dict.fromkeys(tags))
                self.storage.update_paper(paper["id"], {"tags": tags})
                updated_count += 1

        return updated_count

    def delete_tag(self, tag):
        """Delete tag from all papers"""
        if not tag:
            raise ValueError("Tag name cannot be empty")

        # Remove from all papers
        papers = list(self.storage.data["papers"].values())
        updated_count = 0

        for paper in papers:
            tags = paper.get("tags", [])
            if tag in tags:
                tags.remove(tag)
                self.storage.update_paper(paper["id"], {"tags": tags})
                updated_count += 1

        return updated_count

    def merge_tags(self, source_tags, target_tag):
        """Merge multiple tags into one"""
        if not source_tags or not target_tag:
            raise ValueError("Source and target tags cannot be empty")

        normalized_target = self.normalize_tag(target_tag)
        if not normalized_target:
            raise ValueError("Invalid target tag name")

        # Update all papers
        papers = list(self.storage.data["papers"].values())
        updated_count = 0

        for paper in papers:
            tags = paper.get("tags", [])
            has_source_tag = any(tag in source_tags for tag in tags)

            if has_source_tag:
                # Remove source tags and add target tag
                new_tags = [tag for tag in tags if tag not in source_tags]
                if normalized_target not in new_tags:
                    new_tags.append(normalized_target)

                self.storage.update_paper(paper["id"], {"tags": new_tags})
                updated_count += 1

        return updated_count

    def normalize_tag(self, tag):
        """Normalize tag format"""
        if not tag:
            return ""

        # Strip whitespace and convert to lowercase
        normalized = tag.strip().lower()

        # Remove extra spaces
        normalized = " ".join(normalized.split())

        # Check for valid characters (allow letters, numbers, spaces, hyphens, underscores)
        import re

        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", normalized):
            return ""

        # Limit length
        if len(normalized) > 50:
            normalized = normalized[:50].strip()

        return normalized

    def suggest_tags(self, paper_data, limit=5):
        """Suggest tags for a paper based on its content"""
        suggestions = set()

        # Extract potential tags from title
        title = paper_data.get("title", "")
        title_tags = self.extract_tags_from_text(title)
        suggestions.update(title_tags)

        # Extract from abstract
        abstract = paper_data.get("abstract", "")
        abstract_tags = self.extract_tags_from_text(abstract)
        suggestions.update(abstract_tags)

        # Extract from journal name
        journal = self.get_journal_name(paper_data)
        if journal:
            journal_tags = self.extract_tags_from_text(journal)
            suggestions.update(journal_tags)

        # Filter suggestions based on existing popular tags
        popular_tags = self.get_popular_tags(20)
        filtered_suggestions = []

        for suggestion in suggestions:
            # Check if similar to popular tags
            for popular_tag in popular_tags:
                if (
                    suggestion in popular_tag
                    or popular_tag in suggestion
                    or self.are_tags_similar(suggestion, popular_tag)
                ):
                    filtered_suggestions.append(popular_tag)
                    break
            else:
                filtered_suggestions.append(suggestion)

        return filtered_suggestions[:limit]

    def extract_tags_from_text(self, text):
        """Extract potential tags from text"""
        if not text:
            return []

        # Common academic keywords
        keywords = [
            "machine learning",
            "deep learning",
            "neural network",
            "artificial intelligence",
            "computer vision",
            "natural language processing",
            "data mining",
            "big data",
            "algorithm",
            "optimization",
            "classification",
            "regression",
            "clustering",
            "statistics",
            "analysis",
            "model",
            "method",
            "approach",
            "framework",
            "system",
            "application",
            "evaluation",
            "performance",
            "comparison",
            "review",
            "survey",
            "study",
            "research",
            "experiment",
            "case study",
        ]

        text_lower = text.lower()
        found_tags = []

        for keyword in keywords:
            if keyword in text_lower:
                found_tags.append(keyword)

        return found_tags

    def get_journal_name(self, paper_data):
        """Extract journal name from paper"""
        container_title = paper_data.get("container-title", [])
        if isinstance(container_title, list) and container_title:
            return container_title[0]
        elif isinstance(container_title, str):
            return container_title
        return ""

    def are_tags_similar(self, tag1, tag2):
        """Check if two tags are similar"""
        # Simple similarity check
        if not tag1 or not tag2:
            return False

        # Check if one is contained in the other
        if tag1 in tag2 or tag2 in tag1:
            return True

        # Check word overlap
        words1 = set(tag1.split())
        words2 = set(tag2.split())

        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1.intersection(words2))
            min_words = min(len(words1), len(words2))
            similarity = overlap / min_words
            return similarity > 0.5

        return False

    def get_tag_statistics(self):
        """Get tag usage statistics"""
        tag_counts = self.get_tag_usage_count()

        if not tag_counts:
            return {
                "total_tags": 0,
                "total_usage": 0,
                "average_usage": 0,
                "most_used": None,
                "least_used": None,
            }

        total_tags = len(tag_counts)
        total_usage = sum(tag_counts.values())
        average_usage = total_usage / total_tags

        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1])
        most_used = sorted_tags[-1]
        least_used = sorted_tags[0]

        return {
            "total_tags": total_tags,
            "total_usage": total_usage,
            "average_usage": round(average_usage, 2),
            "most_used": most_used,
            "least_used": least_used,
        }

    def cleanup_unused_tags(self):
        """Remove tags that are not used by any papers"""
        # This method would be useful if we stored tags separately
        # Currently tags are stored with papers, so no cleanup needed
        # But we can return count of tags with usage count of 0
        tag_counts = self.get_tag_usage_count()
        unused_tags = [tag for tag, count in tag_counts.items() if count == 0]
        return len(unused_tags)

    def export_tags(self):
        """Export all tags with their usage counts"""
        tag_counts = self.get_tag_usage_count()

        export_data = []
        for tag, count in sorted(tag_counts.items()):
            export_data.append(
                {
                    "tag": tag,
                    "usage_count": count,
                    "papers": self.get_papers_by_tag(tag),
                }
            )

        return export_data
