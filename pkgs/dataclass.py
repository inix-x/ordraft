import os
import sys
import uuid

from dataclasses import dataclass, field


if __name__ == "__main__" or "pkgs" not in sys.modules:
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    )

from .enums import TemplateType, Models

@dataclass
class GenerateDocData:
    url: str
    pdf_path: str
    save_path: str
    selected_template: TemplateType
    custom_prompt: str
    stream: bool = field(default=False)
    model: Models = field(default=Models.deepseek_r1_distill_llama_8b)
    is_reply_included: bool = field(default=False)
    is_custom_prompt: bool = field(default=False)
    
    def validate(self):
        errors = []
        if not isinstance(self.selected_template, TemplateType) or not self.selected_template.value.strip():
            errors.append("Choose a Template")
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
    status: str
    api_url: str = field(default=None)
    model: Models = field(default=Models.deepseek_r1_distill_llama_8b)
    api_response: dict = field(default=None)
    error_occured: object  = field(default=None)

    def validate(self):
        errors = []
        if not self.status.strip():
            errors.append("status cannot be empty.")

        if self.error_occured is not None:
            errors.append(self.error_occured)

        if errors:
            raise ValueError("Validation errors: " + "; ".join(errors))
        
@dataclass
class Document:
    temp_doc_data: GenerateDocData
    doc_payload: DocPayload
    _uuid: str = field(init=False, repr=False)  
    file_name: str = field(default=None)
    _save_filepath: str = field(init=False, repr=False)  

    def __post_init__(self):
        self.save_filepath = ""
        self._uuid = str(uuid.uuid4())

    @property
    def id(self):
        return self._uuid
    
    @id.setter
    def id(self, id: str):
        if not isinstance(id, str):
            raise TypeError(f"ID not str, type: {type(id)}")

        self._uuid = id

    @property
    def save_filepath(self):
        return self._save_filepath

    @save_filepath.setter
    def save_filepath(self, path):
        self._save_filepath = os.path.realpath(path)


@dataclass
class DocumentsCollection:
    def __init__(self, doc_data: list[Document] = []):
        self._doc = {doc_data.id: doc_data for doc_data in doc_data}

    def __getitem__(self, id: str) -> Document:
        return self._doc[id]
    
    def __setitem__(self, id: str, doc: Document):
        self._doc[id] = doc

    def __iter__(self):
        return iter(self._doc.values())
    
    def add(self, doc: Document):
        self._doc[doc.id] = doc

    def remove(self, doc: Document):
        self._doc.pop(doc.id)

    def clear(self):
        self._doc.clear()

    def len(self) -> int:
        return len(self._doc)
        
    def is_empty(self) -> bool:
        """Returns True if the collection has no documents, otherwise False."""
        return len(self._doc) == 0

@dataclass
class UpdateDocData:
    status: str
    name: str
    id: str 
    file_path: str = field(default=None)
    error: object = field(default=None)

    def validate(self):
        errors = []
        if self.id is None:
            errors.append("ID cannot be empty.")
        if not self.status.strip():
            errors.append("status cannot be empty.")

        if self.error is not None:
            errors.append(self.error)
            
        if errors:
            raise ValueError(f"Validation errors: {errors}")

@dataclass
class DataLLM:
    model: str = field(default=Models.deepseek_r1_distill_llama_8b)

@dataclass
class Model:
    model:str

