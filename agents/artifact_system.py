"""
Artifact System - Lightweight agent-to-agent communication following 2025 best practices

This module implements an artifact-based communication system that prevents token bloat
while enabling complex multi-agent workflows. Agents create persistent artifacts that
other agents can reference through lightweight tokens.
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import logging


class ArtifactType(Enum):
    """Types of artifacts that can be created"""
    DATA_REPORT = "data_report"
    ANALYSIS_RESULT = "analysis_result"
    TASK_RESULT = "task_result"
    CODE_OUTPUT = "code_output"
    VALIDATION_REPORT = "validation_report"
    PERFORMANCE_METRICS = "performance_metrics"
    RECOMMENDATIONS = "recommendations"
    ERROR_REPORT = "error_report"
    SYSTEM_STATE = "system_state"


class ArtifactStatus(Enum):
    """Status of artifacts"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass
class HandoffToken:
    """Token for validating agent-to-agent handoffs"""
    token_id: str
    from_agent: str
    to_agent: str
    artifact_refs: List[str]
    context_summary: str
    validation_required: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Artifact:
    """Artifact containing agent output data"""
    artifact_id: str
    artifact_type: ArtifactType
    title: str
    description: str
    content: Dict[str, Any]
    created_by: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    status: ArtifactStatus = ArtifactStatus.ACTIVE
    metadata: Optional[Dict[str, Any]] = None
    related_artifacts: Optional[List[str]] = None
    access_count: int = 0
    
    def to_reference(self) -> Dict[str, Any]:
        """Create a lightweight reference to this artifact"""
        return {
            'artifact_id': self.artifact_id,
            'type': self.artifact_type.value,
            'title': self.title,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'size_bytes': len(json.dumps(self.content)),
            'status': self.status.value
        }


class ArtifactSystem:
    """
    Central artifact management system implementing 2025 best practices:
    
    1. Lightweight references instead of full content transfer
    2. JIT (Just-In-Time) context loading
    3. Automatic cleanup and expiration
    4. HANDOFF_TOKEN validation between agents
    5. Context drift prevention through artifact versioning
    """
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.artifacts: Dict[str, Artifact] = {}
        self.handoff_tokens: Dict[str, HandoffToken] = {}
        self.storage_path = self.project_root / ".agents" / "artifacts"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = self._setup_logging()
        self.max_artifacts = 1000
        self.default_expiry_hours = 24
        
        # Load existing artifacts
        self._load_artifacts()
        
        self.logger.info("Artifact System initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the artifact system"""
        logger = logging.getLogger("mep_ranking.artifacts")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | ARTIFACTS | %(levelname)s | %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _generate_id(self, prefix: str = "artifact") -> str:
        """Generate unique ID for artifacts or tokens"""
        timestamp = str(int(time.time()))
        random_hash = hashlib.md5(f"{timestamp}{time.time()}".encode()).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{random_hash}"
    
    def _load_artifacts(self) -> None:
        """Load existing artifacts from storage"""
        try:
            index_file = self.storage_path / "index.json"
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    artifact_index = json.load(f)
                
                for artifact_id, artifact_data in artifact_index.items():
                    # Load artifact content
                    artifact_file = self.storage_path / f"{artifact_id}.json"
                    if artifact_file.exists():
                        with open(artifact_file, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                        
                        artifact = Artifact(
                            artifact_id=artifact_data['artifact_id'],
                            artifact_type=ArtifactType(artifact_data['artifact_type']),
                            title=artifact_data['title'],
                            description=artifact_data['description'],
                            content=content,
                            created_by=artifact_data['created_by'],
                            created_at=datetime.fromisoformat(artifact_data['created_at']),
                            expires_at=datetime.fromisoformat(artifact_data['expires_at']) if artifact_data.get('expires_at') else None,
                            status=ArtifactStatus(artifact_data.get('status', 'active')),
                            metadata=artifact_data.get('metadata'),
                            related_artifacts=artifact_data.get('related_artifacts'),
                            access_count=artifact_data.get('access_count', 0)
                        )
                        
                        self.artifacts[artifact_id] = artifact
                
                self.logger.info(f"Loaded {len(self.artifacts)} artifacts from storage")
                
        except Exception as e:
            self.logger.warning(f"Failed to load artifacts: {e}")
    
    def _save_artifact(self, artifact: Artifact) -> None:
        """Save artifact to persistent storage"""
        try:
            # Save artifact content
            artifact_file = self.storage_path / f"{artifact.artifact_id}.json"
            with open(artifact_file, 'w', encoding='utf-8') as f:
                json.dump(artifact.content, f, indent=2, default=str)
            
            # Update index
            self._update_index()
            
        except Exception as e:
            self.logger.error(f"Failed to save artifact {artifact.artifact_id}: {e}")
    
    def _update_index(self) -> None:
        """Update the artifact index file"""
        try:
            index = {}
            for artifact_id, artifact in self.artifacts.items():
                index[artifact_id] = {
                    'artifact_id': artifact.artifact_id,
                    'artifact_type': artifact.artifact_type.value,
                    'title': artifact.title,
                    'description': artifact.description,
                    'created_by': artifact.created_by,
                    'created_at': artifact.created_at.isoformat(),
                    'expires_at': artifact.expires_at.isoformat() if artifact.expires_at else None,
                    'status': artifact.status.value,
                    'metadata': artifact.metadata,
                    'related_artifacts': artifact.related_artifacts,
                    'access_count': artifact.access_count
                }
            
            index_file = self.storage_path / "index.json"
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to update artifact index: {e}")
    
    async def create_artifact(self, 
                            artifact_type: ArtifactType,
                            title: str,
                            description: str,
                            content: Dict[str, Any],
                            created_by: str,
                            expires_in_hours: Optional[int] = None,
                            metadata: Optional[Dict[str, Any]] = None,
                            related_artifacts: Optional[List[str]] = None) -> str:
        """
        Create a new artifact and return its ID
        
        Args:
            artifact_type: Type of artifact
            title: Short title for the artifact
            description: Detailed description
            content: Artifact data content
            created_by: Agent that created the artifact
            expires_in_hours: Hours until expiration (default: 24)
            metadata: Additional metadata
            related_artifacts: IDs of related artifacts
            
        Returns:
            Artifact ID
        """
        
        artifact_id = self._generate_id("artifact")
        
        # Set expiration
        expires_at = None
        if expires_in_hours is not None:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        else:
            expires_at = datetime.now() + timedelta(hours=self.default_expiry_hours)
        
        artifact = Artifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            title=title,
            description=description,
            content=content,
            created_by=created_by,
            created_at=datetime.now(),
            expires_at=expires_at,
            metadata=metadata or {},
            related_artifacts=related_artifacts or []
        )
        
        # Store artifact
        self.artifacts[artifact_id] = artifact
        self._save_artifact(artifact)
        
        # Cleanup if needed
        await self._cleanup_artifacts()
        
        self.logger.info(f"Created artifact {artifact_id} of type {artifact_type.value} by {created_by}")
        return artifact_id
    
    async def get_artifact_reference(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get lightweight reference to an artifact (JIT loading)"""
        if artifact_id not in self.artifacts:
            return None
            
        artifact = self.artifacts[artifact_id]
        artifact.access_count += 1
        
        # Check expiration
        if artifact.expires_at and datetime.now() > artifact.expires_at:
            artifact.status = ArtifactStatus.EXPIRED
            self.logger.warning(f"Artifact {artifact_id} has expired")
            return None
        
        reference = artifact.to_reference()
        self.logger.debug(f"Generated reference for artifact {artifact_id}")
        return reference
    
    async def get_artifact_content(self, artifact_id: str, requesting_agent: str) -> Optional[Dict[str, Any]]:
        """Get full artifact content (use sparingly to prevent token bloat)"""
        if artifact_id not in self.artifacts:
            self.logger.warning(f"Artifact {artifact_id} not found")
            return None
            
        artifact = self.artifacts[artifact_id]
        
        # Check expiration
        if artifact.expires_at and datetime.now() > artifact.expires_at:
            artifact.status = ArtifactStatus.EXPIRED
            self.logger.warning(f"Artifact {artifact_id} has expired")
            return None
        
        artifact.access_count += 1
        self.logger.info(f"Agent {requesting_agent} accessed content of artifact {artifact_id}")
        return artifact.content
    
    async def create_handoff_token(self,
                                 from_agent: str,
                                 to_agent: str,
                                 artifact_refs: List[str],
                                 context_summary: str,
                                 validation_required: bool = True) -> str:
        """Create a handoff token for agent-to-agent communication"""
        
        token_id = self._generate_id("handoff")
        
        token = HandoffToken(
            token_id=token_id,
            from_agent=from_agent,
            to_agent=to_agent,
            artifact_refs=artifact_refs,
            context_summary=context_summary,
            validation_required=validation_required
        )
        
        self.handoff_tokens[token_id] = token
        
        self.logger.info(f"Created handoff token {token_id} from {from_agent} to {to_agent}")
        return token_id
    
    async def validate_handoff_token(self, token_id: str, receiving_agent: str) -> Optional[HandoffToken]:
        """Validate a handoff token and return it if valid"""
        if token_id not in self.handoff_tokens:
            self.logger.error(f"Handoff token {token_id} not found")
            return None
        
        token = self.handoff_tokens[token_id]
        
        if token.to_agent != receiving_agent:
            self.logger.error(f"Handoff token {token_id} is not for agent {receiving_agent}")
            return None
        
        # Check if token is still valid (1 hour expiry)
        if datetime.now() - token.created_at > timedelta(hours=1):
            self.logger.error(f"Handoff token {token_id} has expired")
            del self.handoff_tokens[token_id]
            return None
        
        self.logger.info(f"Validated handoff token {token_id} for agent {receiving_agent}")
        return token
    
    async def list_artifacts(self, 
                           created_by: Optional[str] = None,
                           artifact_type: Optional[ArtifactType] = None,
                           active_only: bool = True) -> List[Dict[str, Any]]:
        """List artifacts with optional filtering"""
        
        references = []
        for artifact in self.artifacts.values():
            # Apply filters
            if created_by and artifact.created_by != created_by:
                continue
            if artifact_type and artifact.artifact_type != artifact_type:
                continue
            if active_only and artifact.status != ArtifactStatus.ACTIVE:
                continue
            
            references.append(artifact.to_reference())
        
        # Sort by creation time (newest first)
        references.sort(key=lambda x: x['created_at'], reverse=True)
        
        return references
    
    async def _cleanup_artifacts(self) -> None:
        """Clean up expired and excess artifacts"""
        try:
            current_time = datetime.now()
            cleanup_count = 0
            
            # Mark expired artifacts
            for artifact in self.artifacts.values():
                if artifact.expires_at and current_time > artifact.expires_at:
                    artifact.status = ArtifactStatus.EXPIRED
                    cleanup_count += 1
            
            # If too many artifacts, archive oldest ones
            if len(self.artifacts) > self.max_artifacts:
                sorted_artifacts = sorted(
                    self.artifacts.values(),
                    key=lambda a: a.created_at
                )
                
                excess_count = len(self.artifacts) - self.max_artifacts
                for artifact in sorted_artifacts[:excess_count]:
                    artifact.status = ArtifactStatus.ARCHIVED
                    cleanup_count += 1
            
            if cleanup_count > 0:
                self._update_index()
                self.logger.info(f"Cleaned up {cleanup_count} artifacts")
                
        except Exception as e:
            self.logger.error(f"Error during artifact cleanup: {e}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get artifact system statistics"""
        stats = {
            'total_artifacts': len(self.artifacts),
            'active_artifacts': len([a for a in self.artifacts.values() if a.status == ArtifactStatus.ACTIVE]),
            'expired_artifacts': len([a for a in self.artifacts.values() if a.status == ArtifactStatus.EXPIRED]),
            'active_handoff_tokens': len(self.handoff_tokens),
            'artifact_types': {},
            'agents_active': set()
        }
        
        for artifact in self.artifacts.values():
            artifact_type = artifact.artifact_type.value
            if artifact_type not in stats['artifact_types']:
                stats['artifact_types'][artifact_type] = 0
            stats['artifact_types'][artifact_type] += 1
            stats['agents_active'].add(artifact.created_by)
        
        stats['agents_active'] = len(stats['agents_active'])
        
        return stats