from dataclasses import dataclass, field
from typing import List


@dataclass
class DocumentMetadata:
    document_id: str
    title: str
    department: str
    section: str
    document_type: str
    version: str
    access_level: str


@dataclass
class Section:
    heading: str
    content: str


@dataclass
class TechNovaDocument:
    content: str
    metadata: DocumentMetadata
    sections: List[Section] = field(default_factory=list)
    
@dataclass
class ParentChunk:
    parent_id: str
    content: str
    metadata: DocumentMetadata


@dataclass
class ChildChunk:
    child_id: str
    parent_id: str
    content: str
    metadata: DocumentMetadata