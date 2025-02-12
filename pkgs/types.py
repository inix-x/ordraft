from uuid import UUID

from dataclasses import dataclass, field


from .enums import TemplateType

@dataclass
class GenerateDocData:
    url: str
    port: str | None
    pdf_path: str
    save_path: str
    selected_template: TemplateType
    custom_prompt: str
    is_reply_included: bool = field(default=False)
    is_custom_prompt: bool = field(default=False)

    def validate(self):
        errors = []
        if not self.url.strip():
            errors.append("Name cannot be empty.")
        if not self.pdf_path.strip():
            errors.append("Document file cannot be empty.")
        if not self.save_path.strip():
            errors.append("Save location cannot be empty.")
        if not self.custom_prompt.strip() and self.is_custom_prompt:
            errors.append("Custom prompt cannot be empty.")
        if errors:
            raise ValueError("Validation errors: " + "; ".join(errors))

@dataclass
class DocPayload:
    uuid: UUID
    status: str
    api_url: str | None = field(default=None)
    api_port: str | None = field(default=None)
    api_response: dict | None = field(default=None)
    error_occured: object | None  = field(default=None)

    def validate(self):
        if self.error_occured is not None:
            raise ValueError(f"Validation errors: {self.error_occured}")
        
@dataclass
class Document:
    uuid: UUID
    temp_doc_data: GenerateDocData
    doc_payload: DocPayload
    file_name: str | None = field(default=None)
    save_filepath: str | None = field(default=None)


@dataclass
class DocumentsCollection:
    def __init__(self, doc_data: list[Document] = []):
        self._doc = {doc_data.uuid: doc_data for doc_data in doc_data}

    def __getitem__(self, uuid: UUID) -> Document:
        return self._doc[uuid]
    
    def __setitem__(self, uuid: UUID, doc: Document):
        self._doc[uuid] = doc

    def __iter__(self):
        return iter(self._doc.values())
    
    def add(self, doc: Document):
        self._doc[doc.uuid] = doc

    def remove(self, doc: Document):
        self._doc.pop(doc.uuid)

    def clear(self):
        self._doc.clear()

    def len(self) -> int:
        return len(self._doc)
        
    def is_empty(self) -> bool:
        """Returns True if the collection has no documents, otherwise False."""
        return len(self._doc) == 0


@dataclass
class UpdateDocData:
    uuid: UUID
    status: str
    name: str
    file_path: str | None = field(default=None)
    error: object | None = field(default=None)

@dataclass
class DataLLM:
    model: str = field(default="deepseek-r1-distill-qwen-7b")

