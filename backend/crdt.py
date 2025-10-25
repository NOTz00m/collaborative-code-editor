"""
CRDT (Conflict-free Replicated Data Type) implementation for collaborative editing.
This implements a simple character-wise CRDT using Yjs-compatible operations.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import time
from collections import defaultdict


@dataclass
class Operation:
    """Represents a single edit operation."""
    op_type: str  # 'insert' or 'delete'
    position: int
    content: str = ""
    client_id: str = ""
    timestamp: float = field(default_factory=time.time)
    version: int = 0
    
    def to_dict(self) -> dict:
        """Convert operation to dictionary."""
        return {
            'type': self.op_type,
            'position': self.position,
            'content': self.content,
            'clientId': self.client_id,
            'timestamp': self.timestamp,
            'version': self.version
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Operation':
        """Create operation from dictionary."""
        return Operation(
            op_type=data.get('type', 'insert'),
            position=data.get('position', 0),
            content=data.get('content', ''),
            client_id=data.get('clientId', ''),
            timestamp=data.get('timestamp', time.time()),
            version=data.get('version', 0)
        )


class CRDT:
    """
    Simple CRDT implementation for collaborative text editing.
    Uses operation transformation to handle concurrent edits.
    """
    
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.content: str = ""
        self.operations: List[Operation] = []
        self.version: int = 0
        self.client_versions: Dict[str, int] = defaultdict(int)
    
    def apply_operation(self, operation: Operation) -> bool:
        """
        Apply an operation to the document.
        
        Args:
            operation: The operation to apply
            
        Returns:
            True if operation was applied successfully
        """
        try:
            # Transform operation based on concurrent operations
            transformed_op = self._transform_operation(operation)
            
            if transformed_op.op_type == 'insert':
                pos = min(transformed_op.position, len(self.content))
                self.content = (
                    self.content[:pos] + 
                    transformed_op.content + 
                    self.content[pos:]
                )
            elif transformed_op.op_type == 'delete':
                start = min(transformed_op.position, len(self.content))
                length = len(transformed_op.content)
                end = min(start + length, len(self.content))
                self.content = self.content[:start] + self.content[end:]
            
            # Update version tracking
            self.version += 1
            transformed_op.version = self.version
            self.operations.append(transformed_op)
            self.client_versions[operation.client_id] = self.version
            
            return True
            
        except Exception as e:
            print(f"Error applying operation: {e}")
            return False
    
    def _transform_operation(self, operation: Operation) -> Operation:
        """
        Transform an operation based on concurrent operations.
        Implements Operational Transformation (OT) algorithm.
        
        Args:
            operation: The operation to transform
            
        Returns:
            Transformed operation
        """
        # Get operations that happened concurrently
        client_version = self.client_versions.get(operation.client_id, 0)
        concurrent_ops = [
            op for op in self.operations 
            if op.version > client_version
        ]
        
        # Transform position based on concurrent operations
        transformed_position = operation.position
        
        for concurrent_op in concurrent_ops:
            if concurrent_op.op_type == 'insert':
                if concurrent_op.position <= transformed_position:
                    transformed_position += len(concurrent_op.content)
            elif concurrent_op.op_type == 'delete':
                if concurrent_op.position < transformed_position:
                    transformed_position -= min(
                        len(concurrent_op.content),
                        transformed_position - concurrent_op.position
                    )
        
        return Operation(
            op_type=operation.op_type,
            position=max(0, transformed_position),
            content=operation.content,
            client_id=operation.client_id,
            timestamp=operation.timestamp
        )
    
    def get_operations_since(self, version: int) -> List[Operation]:
        """Get all operations since a specific version."""
        return [op for op in self.operations if op.version > version]
    
    def get_state(self) -> dict:
        """Get the current state of the document."""
        return {
            'documentId': self.document_id,
            'content': self.content,
            'version': self.version
        }
    
    def set_content(self, content: str) -> None:
        """Set the initial content of the document."""
        self.content = content
        self.version += 1
