"""
Storage Manager for DOI Citation Manager
- AppData/Roaming에 데이터 저장
- 향상된 오류 처리 및 로깅
"""
import json
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from config import DATABASE_FILE, BACKUP_DIR, SETTINGS_FILE, USER_DATA_DIR, LOG_FILE

# 로깅 설정
def setup_logging():
    """로깅 설정"""
    try:
        # 로그 디렉토리 생성
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    except Exception as e:
        print(f"Warning: Could not setup logging: {e}")

# 로깅 초기화
setup_logging()
logger = logging.getLogger(__name__)

class Storage:
    """Manager for local JSON data storage"""
    
    def __init__(self):
        self.database_file = DATABASE_FILE
        self.settings_file = SETTINGS_FILE
        self.backup_dir = Path(BACKUP_DIR)
        self.user_data_dir = Path(USER_DATA_DIR)
        
        # 디렉토리 생성 확인
        self.ensure_directories()
        
        # 데이터 로드
        self.data = self.load_data()
        self.settings = self.load_settings()
        
        logger.info(f"Storage initialized. Data directory: {self.user_data_dir}")
        
    def ensure_directories(self):
        """필요한 디렉토리들이 존재하는지 확인하고 생성"""
        directories = [
            self.user_data_dir,
            self.database_file.parent,
            self.settings_file.parent,
            self.backup_dir
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Directory ensured: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                raise
        
    def load_data(self):
        """Load data from JSON file"""
        if self.database_file.exists():
            try:
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Validate and migrate data structure if needed
                data = self.validate_data_structure(data)
                logger.info(f"Data loaded successfully from {self.database_file}")
                return data
                
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading database: {e}")
                # 백업에서 복구 시도
                backup_data = self.try_restore_from_backup()
                if backup_data:
                    return backup_data
                else:
                    return self.create_default_data()
        else:
            logger.info("Database file not found, creating default data")
            return self.create_default_data()
    
    def try_restore_from_backup(self):
        """백업에서 데이터 복구 시도"""
        try:
            backup_files = list(self.backup_dir.glob("backup_*.json"))
            if not backup_files:
                logger.warning("No backup files found")
                return None
                
            # 가장 최근 백업 파일 찾기
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"Attempting to restore from backup: {latest_backup}")
            
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info("Successfully restored from backup")
            return self.validate_data_structure(data)
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return None
    
    def load_settings(self):
        """Load application settings"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info("Settings loaded successfully")
                return settings
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                return self.create_default_settings()
        else:
            logger.info("Settings file not found, creating default settings")
            return self.create_default_settings()
    
    def create_default_settings(self):
        """Create default application settings"""
        settings = {
            'version': '1.0.0',
            'theme': 'light',
            'default_citation_format': 'APA',
            'auto_backup': True,
            'backup_interval_days': 7,
            'window_size': [1400, 900],
            'window_position': None,
            'splitter_sizes': [300, 900],
            'recent_dois': [],
            'created': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
        self.save_settings(settings)
        return settings
        
    def create_default_data(self):
        """Create default data structure"""
        data = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'projects': [],
            'papers': {},
            'tags': [],
            'settings': {
                'theme': 'light',
                'default_citation_format': 'APA',
                'auto_backup': True
            }
        }
        
        # 기본 프로젝트 생성
        try:
            default_project = {
                'id': self.generate_id(),
                'name': 'My Papers',
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'papers': []
            }
            data['projects'].append(default_project)
            logger.info("Created default project")
        except Exception as e:
            logger.error(f"Error creating default project: {e}")
        
        return data
        
    def validate_data_structure(self, data):
        """Validate and fix data structure"""
        # Ensure required keys exist
        required_keys = ['version', 'projects', 'papers', 'tags', 'settings']
        for key in required_keys:
            if key not in data:
                if key == 'projects':
                    data[key] = []
                elif key == 'papers':
                    data[key] = {}
                elif key == 'tags':
                    data[key] = []
                elif key == 'settings':
                    data[key] = {}
                else:
                    data[key] = ''
                    
        # Ensure projects have required fields
        for project in data['projects']:
            if 'id' not in project:
                project['id'] = self.generate_id()
            if 'name' not in project:
                project['name'] = 'Unnamed Project'
            if 'created' not in project:
                project['created'] = datetime.now().isoformat()
            if 'papers' not in project:
                project['papers'] = []
                
        # Update last modified
        data['last_modified'] = datetime.now().isoformat()
        
        return data
        
    def save_data(self):
        """Save data to JSON file"""
        try:
            # Create backup before saving
            if self.data.get('settings', {}).get('auto_backup', True):
                self.create_backup()
                
            # Update last modified
            self.data['last_modified'] = datetime.now().isoformat()
            
            # Write to temporary file first
            temp_file = self.database_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                
            # Move temporary file to actual file (atomic operation)
            if os.name == 'nt':  # Windows
                if self.database_file.exists():
                    self.database_file.unlink()
                temp_file.rename(self.database_file)
            else:  # Unix-like systems
                temp_file.rename(self.database_file)
                
            logger.info("Data saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            # 임시 파일 정리
            temp_file = self.database_file.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            return False
    
    def save_settings(self, settings=None):
        """Save application settings"""
        if settings is None:
            settings = self.settings
            
        try:
            settings['last_modified'] = datetime.now().isoformat()
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
            self.settings = settings
            logger.info("Settings saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
            
    def create_backup(self):
        """Create backup of current data"""
        if not self.database_file.exists():
            return
            
        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"backup_{timestamp}.json"
            
            # Copy current database to backup
            shutil.copy2(self.database_file, backup_file)
            logger.info(f"Backup created: {backup_file}")
            
            # Keep only recent backups
            self.cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            
    def cleanup_old_backups(self, keep_count=10):
        """Keep only the most recent backups"""
        try:
            backup_files = list(self.backup_dir.glob("backup_*.json"))
            if len(backup_files) > keep_count:
                # Sort by modification time, newest first
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Remove old backups
                for old_backup in backup_files[keep_count:]:
                    old_backup.unlink()
                    logger.debug(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
            
    def generate_id(self):
        """Generate unique ID"""
        from uuid import uuid4
        return str(uuid4())
        
    # Project methods
    def create_project(self, name):
        """Create new project"""
        project = {
            'id': self.generate_id(),
            'name': name,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'papers': []
        }
        
        self.data['projects'].append(project)
        self.save_data()
        logger.info(f"Created project: {name}")
        return project
        
    def get_all_projects(self):
        """Get all projects"""
        return self.data['projects']
        
    def get_project_by_id(self, project_id):
        """Get project by ID"""
        for project in self.data['projects']:
            if project['id'] == project_id:
                return project
        return None
        
    def update_project(self, project_id, updates):
        """Update project"""
        project = self.get_project_by_id(project_id)
        if project:
            project.update(updates)
            project['modified'] = datetime.now().isoformat()
            self.save_data()
            return project
        return None
        
    def delete_project(self, project_id):
        """Delete project and its papers"""
        project = self.get_project_by_id(project_id)
        if project:
            # Remove papers from papers collection
            for paper_id in project.get('papers', []):
                if paper_id in self.data['papers']:
                    del self.data['papers'][paper_id]
                    
            # Remove project
            self.data['projects'] = [p for p in self.data['projects'] if p['id'] != project_id]
            self.save_data()
            logger.info(f"Deleted project: {project.get('name', project_id)}")
            return True
        return False
        
    def rename_project(self, project_id, new_name):
        """Rename project"""
        return self.update_project(project_id, {'name': new_name})
        
    # Paper methods
    def add_paper(self, paper_data):
        """Add paper to collection"""
        paper_id = paper_data.get('id') or self.generate_id()
        paper_data['id'] = paper_id
        paper_data['added'] = datetime.now().isoformat()
        
        self.data['papers'][paper_id] = paper_data
        self.save_data()
        logger.info(f"Added paper: {paper_data.get('title', paper_id)}")
        return paper_data
        
    def get_paper_by_id(self, paper_id):
        """Get paper by ID"""
        return self.data['papers'].get(paper_id)
        
    def update_paper(self, paper_id, updates):
        """Update paper"""
        if paper_id in self.data['papers']:
            self.data['papers'][paper_id].update(updates)
            self.data['papers'][paper_id]['modified'] = datetime.now().isoformat()
            self.save_data()
            return self.data['papers'][paper_id]
        return None
        
    def delete_paper(self, paper_id):
        """Delete paper"""
        if paper_id in self.data['papers']:
            # Remove from all projects
            for project in self.data['projects']:
                if paper_id in project.get('papers', []):
                    project['papers'].remove(paper_id)
                    
            # Remove from papers collection
            paper_title = self.data['papers'][paper_id].get('title', paper_id)
            del self.data['papers'][paper_id]
            self.save_data()
            logger.info(f"Deleted paper: {paper_title}")
            return True
        return False
        
    def add_paper_to_project(self, project_id, paper_data):
        """Add paper to specific project"""
        project = self.get_project_by_id(project_id)
        if not project:
            return None
            
        # Add paper to collection if not exists
        paper = self.add_paper(paper_data)
        paper_id = paper['id']
        
        # Add paper to project if not already there
        if paper_id not in project.get('papers', []):
            if 'papers' not in project:
                project['papers'] = []
            project['papers'].append(paper_id)
            project['modified'] = datetime.now().isoformat()
            self.save_data()
            
        return paper
        
    def remove_paper_from_project(self, project_id, paper_id):
        """Remove paper from project (but keep in collection)"""
        project = self.get_project_by_id(project_id)
        if project and paper_id in project.get('papers', []):
            project['papers'].remove(paper_id)
            project['modified'] = datetime.now().isoformat()
            self.save_data()
            return True
        return False
        
    def get_papers_in_project(self, project_id):
        """Get all papers in project"""
        project = self.get_project_by_id(project_id)
        if not project:
            return []
            
        papers = []
        for paper_id in project.get('papers', []):
            paper = self.get_paper_by_id(paper_id)
            if paper:
                papers.append(paper)
                
        return papers
        
    # Search methods
    def search_papers(self, query, project_id=None):
        """Search papers by title, authors, or content"""
        if not query:
            return []
            
        query = query.lower()
        results = []
        
        # Determine which papers to search
        if project_id:
            papers_to_search = self.get_papers_in_project(project_id)
        else:
            papers_to_search = list(self.data['papers'].values())
            
        for paper in papers_to_search:
            # Search in title
            title = paper.get('title', '').lower()
            if query in title:
                results.append(paper)
                continue
                
            # Search in authors
            authors = paper.get('authors', [])
            author_text = ' '.join([
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in authors if isinstance(a, dict)
            ]).lower()
            if query in author_text:
                results.append(paper)
                continue
                
            # Search in abstract
            abstract = paper.get('abstract', '').lower()
            if query in abstract:
                results.append(paper)
                continue
                
            # Search in tags
            tags = paper.get('tags', [])
            tag_text = ' '.join(tags).lower()
            if query in tag_text:
                results.append(paper)
                continue
                
            # Search in notes
            notes = paper.get('notes', '').lower()
            if query in notes:
                results.append(paper)
                continue
                
        return results
        
    # Tag methods
    def get_all_tags(self):
        """Get all unique tags"""
        tags = set()
        for paper in self.data['papers'].values():
            paper_tags = paper.get('tags', [])
            tags.update(paper_tags)
        return sorted(list(tags))
        
    def get_papers_by_tag(self, tag):
        """Get papers with specific tag"""
        results = []
        for paper in self.data['papers'].values():
            if tag in paper.get('tags', []):
                results.append(paper)
        return results
        
    # Settings methods
    def get_setting(self, key, default=None):
        """Get setting value"""
        return self.settings.get(key, default)
        
    def set_setting(self, key, value):
        """Set setting value"""
        self.settings[key] = value
        self.save_settings()
        
    def get_all_settings(self):
        """Get all settings"""
        return self.settings.copy()
        
    def update_settings(self, updates):
        """Update multiple settings"""
        self.settings.update(updates)
        self.save_settings()
        
    # Utility methods
    def save_all(self):
        """Force save all data and settings"""
        data_saved = self.save_data()
        settings_saved = self.save_settings()
        return data_saved and settings_saved
        
    def get_statistics(self):
        """Get database statistics"""
        return {
            'projects': len(self.data['projects']),
            'papers': len(self.data['papers']),
            'tags': len(self.get_all_tags()),
            'last_modified': self.data.get('last_modified'),
            'created': self.data.get('created'),
            'data_directory': str(self.user_data_dir),
            'database_size_mb': round(self.database_file.stat().st_size / (1024*1024), 2) if self.database_file.exists() else 0
        }
        
    def export_data(self, export_path):
        """Export all data to specified path"""
        try:
            export_data = {
                'export_info': {
                    'exported_at': datetime.now().isoformat(),
                    'app_version': '1.0.0',
                    'format_version': '1.0'
                },
                'data': self.data,
                'settings': self.settings
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Data exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
            
    def import_data(self, import_path, merge=False):
        """Import data from specified path"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
                
            if 'data' in imported:
                imported_data = imported['data']
            else:
                # Assume it's raw data
                imported_data = imported
                
            if merge:
                # Merge with existing data
                self.merge_imported_data(imported_data)
            else:
                # Replace existing data
                self.data = self.validate_data_structure(imported_data)
                
            self.save_data()
            logger.info(f"Data imported from: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
            
    def merge_imported_data(self, imported_data):
        """Merge imported data with existing data"""
        # Merge projects (avoid duplicates by name)
        existing_project_names = {p['name'] for p in self.data['projects']}
        
        for project in imported_data.get('projects', []):
            if project['name'] not in existing_project_names:
                project['id'] = self.generate_id()  # Generate new ID
                self.data['projects'].append(project)
                
        # Merge papers (avoid duplicates by DOI)
        existing_dois = {p.get('DOI') for p in self.data['papers'].values() if p.get('DOI')}
        
        for paper_id, paper in imported_data.get('papers', {}).items():
            paper_doi = paper.get('DOI')
            if not paper_doi or paper_doi not in existing_dois:
                new_paper_id = self.generate_id()
                paper['id'] = new_paper_id
                self.data['papers'][new_paper_id] = paper
                
    def get_data_directory_info(self):
        """Get information about data directory"""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.user_data_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
                    
            return {
                'directory': str(self.user_data_dir),
                'exists': self.user_data_dir.exists(),
                'total_size_mb': round(total_size / (1024*1024), 2),
                'file_count': file_count,
                'writable': os.access(self.user_data_dir, os.W_OK),
                'subdirectories': [
                    {'name': 'data', 'path': str(self.database_file.parent), 'exists': self.database_file.parent.exists()},
                    {'name': 'backups', 'path': str(self.backup_dir), 'exists': self.backup_dir.exists()},
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting directory info: {e}")
            return {'error': str(e)}
            
    def cleanup_data(self):
        """Clean up orphaned data and optimize storage"""
        cleaned_items = {
            'orphaned_papers': 0,
            'empty_projects': 0,
            'invalid_references': 0
        }
        
        try:
            # Find papers that are not referenced by any project
            referenced_paper_ids = set()
            for project in self.data['projects']:
                referenced_paper_ids.update(project.get('papers', []))
                
            # Remove orphaned papers
            orphaned_papers = []
            for paper_id in list(self.data['papers'].keys()):
                if paper_id not in referenced_paper_ids:
                    orphaned_papers.append(paper_id)
                    
            for paper_id in orphaned_papers:
                del self.data['papers'][paper_id]
                cleaned_items['orphaned_papers'] += 1
                
            # Clean up invalid paper references in projects
            for project in self.data['projects']:
                valid_papers = []
                for paper_id in project.get('papers', []):
                    if paper_id in self.data['papers']:
                        valid_papers.append(paper_id)
                    else:
                        cleaned_items['invalid_references'] += 1
                project['papers'] = valid_papers
                
            # Remove empty projects (optional - you might want to keep them)
            # self.data['projects'] = [p for p in self.data['projects'] if p.get('papers')]
            
            if sum(cleaned_items.values()) > 0:
                self.save_data()
                logger.info(f"Data cleanup completed: {cleaned_items}")
                
            return cleaned_items
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            return {'error': str(e)}