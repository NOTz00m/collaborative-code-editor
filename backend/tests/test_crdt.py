"""
Unit tests for CRDT implementation.
"""
import pytest
from crdt import CRDT, Operation


class TestCRDT:
    """Test cases for CRDT functionality."""
    
    def test_insert_operation(self):
        """Test basic insert operation."""
        crdt = CRDT("test-doc")
        
        operation = Operation(
            op_type='insert',
            position=0,
            content='Hello',
            client_id='user1'
        )
        
        assert crdt.apply_operation(operation) is True
        assert crdt.content == 'Hello'
        assert crdt.version == 1
    
    def test_delete_operation(self):
        """Test basic delete operation."""
        crdt = CRDT("test-doc")
        crdt.content = "Hello World"
        
        operation = Operation(
            op_type='delete',
            position=6,
            content='World',
            client_id='user1'
        )
        
        assert crdt.apply_operation(operation) is True
        assert crdt.content == 'Hello '
    
    def test_concurrent_inserts(self):
        """Test concurrent insert operations from different users."""
        crdt = CRDT("test-doc")
        
        # User 1 inserts 'A' at position 0
        op1 = Operation(
            op_type='insert',
            position=0,
            content='A',
            client_id='user1'
        )
        crdt.apply_operation(op1)
        
        # User 2 inserts 'B' at position 0 (concurrent with op1)
        op2 = Operation(
            op_type='insert',
            position=0,
            content='B',
            client_id='user2'
        )
        crdt.apply_operation(op2)
        
        # Both operations should be applied
        assert 'A' in crdt.content
        assert 'B' in crdt.content
        assert crdt.version == 2
    
    def test_operation_transformation(self):
        """Test operational transformation for concurrent edits."""
        crdt = CRDT("test-doc")
        crdt.content = "Hello"
        
        # User 1 inserts ' World' at position 5
        op1 = Operation(
            op_type='insert',
            position=5,
            content=' World',
            client_id='user1'
        )
        crdt.apply_operation(op1)
        
        # User 2 tries to insert '!' at position 5 (based on old state)
        # Should be transformed to position 11
        op2 = Operation(
            op_type='insert',
            position=5,
            content='!',
            client_id='user2'
        )
        crdt.apply_operation(op2)
        
        assert crdt.content == 'Hello World!'
    
    def test_get_operations_since(self):
        """Test retrieving operations since a specific version."""
        crdt = CRDT("test-doc")
        
        for i in range(5):
            op = Operation(
                op_type='insert',
                position=i,
                content=str(i),
                client_id='user1'
            )
            crdt.apply_operation(op)
        
        ops = crdt.get_operations_since(2)
        assert len(ops) == 3
        assert all(op.version > 2 for op in ops)
    
    def test_get_state(self):
        """Test getting document state."""
        crdt = CRDT("test-doc")
        crdt.content = "Test content"
        
        state = crdt.get_state()
        assert state['documentId'] == 'test-doc'
        assert state['content'] == 'Test content'
        assert 'version' in state
    
    def test_set_content(self):
        """Test setting initial content."""
        crdt = CRDT("test-doc")
        crdt.set_content("Initial content")
        
        assert crdt.content == "Initial content"
        assert crdt.version == 1
    
    def test_delete_at_boundary(self):
        """Test delete operation at document boundaries."""
        crdt = CRDT("test-doc")
        crdt.content = "Hello"
        
        # Delete beyond document length should be safe
        op = Operation(
            op_type='delete',
            position=3,
            content='loWorld',  # Longer than remaining content
            client_id='user1'
        )
        crdt.apply_operation(op)
        
        assert crdt.content == 'Hel'
    
    def test_delete_with_placeholder_content(self):
        """Test delete operation with placeholder content (simulating frontend fix)."""
        crdt = CRDT("test-doc")
        crdt.content = "Hello World"
        
        # Frontend sends placeholder content with correct length
        # This simulates the fix where we use '\0'.repeat(rangeLength)
        op = Operation(
            op_type='delete',
            position=6,
            content='\0\0\0\0\0',  # 5 null characters representing 5 deleted chars
            client_id='user1'
        )
        crdt.apply_operation(op)
        
        # Should delete 5 characters starting at position 6
        assert crdt.content == 'Hello '
        assert len(crdt.content) == 6
    
    def test_insert_at_invalid_position(self):
        """Test insert at position beyond document length."""
        crdt = CRDT("test-doc")
        crdt.content = "Hi"
        
        # Insert at position beyond length should append
        op = Operation(
            op_type='insert',
            position=100,
            content=' there',
            client_id='user1'
        )
        crdt.apply_operation(op)
        
        assert crdt.content == 'Hi there'


class TestOperation:
    """Test cases for Operation class."""
    
    def test_operation_to_dict(self):
        """Test converting operation to dictionary."""
        op = Operation(
            op_type='insert',
            position=5,
            content='test',
            client_id='user1',
            version=1
        )
        
        data = op.to_dict()
        assert data['type'] == 'insert'
        assert data['position'] == 5
        assert data['content'] == 'test'
        assert data['clientId'] == 'user1'
        assert data['version'] == 1
    
    def test_operation_from_dict(self):
        """Test creating operation from dictionary."""
        data = {
            'type': 'delete',
            'position': 3,
            'content': 'abc',
            'clientId': 'user2',
            'version': 2
        }
        
        op = Operation.from_dict(data)
        assert op.op_type == 'delete'
        assert op.position == 3
        assert op.content == 'abc'
        assert op.client_id == 'user2'
        assert op.version == 2
