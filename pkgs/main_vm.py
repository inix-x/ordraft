import os
import sys
import traceback
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

if __name__ == "__main__" or "pkgs" not in sys.modules:
    test = sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    )
    print(test)
    
from pkgs.api import ApiWorker, ModelLLM
from pkgs.placeholder_replacer import WordPlaceholderReplacer
from pkgs.dataclass import GenerateDocData, DocPayload, DocumentsCollection, Document, UpdateDocData
from pkgs.misc import Data
from pkgs.enums import TemplateFile
from pkgs.list_widget import CustomListItem

class MainViewModel(QObject):
    errorOccured = pyqtSignal(str)
    taskFinished = pyqtSignal(object)
    docGenerated = pyqtSignal()
    processing_finished = pyqtSignal(bool)
    updateDocStatus = pyqtSignal(Document)
    modelProcessed = pyqtSignal(Document)
    docEvents = pyqtSignal(UpdateDocData, str)
    docOpened = pyqtSignal(str, object)

    def __init__(self, data_model: Data = None):
        super().__init__()

        self._data_model = data_model
        self.word_processor = WordPlaceholderReplacer()

        self._documents = DocumentsCollection()

        self._doc_map = {}
        # Agent
        self._setup_agent()

    @property
    def documents(self) -> DocumentsCollection:
        return self._documents
    
    @property
    def doc_ui_map(self):
        return self._doc_map

    def main_handler(self, data: GenerateDocData) -> tuple[bool, object]:
        template_filepath = None
        doc_payload = None
        try:
            data.validate()
            doc_payload = DocPayload(
                status="Queued",
                api_url=data.url,
                model=data.model
            )
            doc_payload.validate()
            document = Document(
                temp_doc_data=data,
                doc_payload=doc_payload
            )
            doc_status = UpdateDocData(
                id=document.id,
                status="Queued",
                name=os.path.basename(data.pdf_path)[0]
            )
            self.documents.add(document)

            self.docEvents.emit(doc_status, document.id)
            template_file = TemplateFile.get_template_file(data.selected_template, data.is_reply_included)
            template_filepath = os.path.join(
                self._data_model.app_data_path, template_file
            )
        except Exception as ve:
            print(traceback.format_exc())
            self.errorOccured.emit(str(ve))
            return False, ve
        try:
            self.word_processor.template_filepath = template_filepath
            self._api_worker.add_task(data=document)
            return True, None
        except Exception as e:
            print(traceback.format_exc())
            return False, e

    # -----Private-----
    def _handle_document_generation(self, doc: Document):
        try:
            # doc.validate()
            self.documents[doc.id] = doc
            doc_status = UpdateDocData(
                id=doc.id,
                status="Generating",
                name=doc.file_name,
            )
            self.docEvents.emit(doc_status, doc.id)

            result: Document = self.word_processor.draft_dismissal(doc)
            if isinstance(result.doc_payload.error_occured, Exception):
                raise ValueError(f"Document: {result.doc_payload.error_occured}")

            document: Document = result
            doc_status = UpdateDocData(
                id=document.id,
                status="Done",
                name=document.file_name,
            )

            self.docEvents.emit(doc_status, document.id)
        except Exception as e:
            doc_status = UpdateDocData(
                id=doc.id,
                status="Error",
                name=doc.file_name,
                error=e
            )
            self.docEvents.emit(doc_status, doc.id)
        finally:
            self._api_worker.allow_next_task()
    
    @pyqtSlot(Document)
    def _handle_status_changed(self, doc: Document):
        try:
            self._documents[doc.id] = doc
            
            path = Path(doc.save_filepath)
            if path.is_file():
                return

            doc_status = UpdateDocData(
                id=doc.id,
                status=doc.doc_payload.status,
                name=doc.file_name,
                error=doc.doc_payload.error_occured
            )

            if doc.doc_payload.error_occured is not None:
                doc_status.status = "Error"
                doc_status.error = doc.doc_payload.error_occured
                self.docEvents.emit(doc_status, doc.id)

            if doc.doc_payload.status == "Processed":
                self._handle_document_generation(doc)
            else:
                self.docEvents.emit(doc_status, doc.id)

        except Exception as e:
            print(f"{e}: {traceback.format_exc()}")
        
    def _setup_agent(self):
        self._api_worker = ApiWorker(ModelLLM())

        self._thread = QThread()
        self._api_worker.moveToThread(self._thread)
        self._thread.started.connect(self._api_worker.run)
        self._api_worker.statusChanged.connect(self._handle_status_changed)
        self._api_worker.finished.connect(self._thread.quit)

        self._thread.start()

    def _stop_agent(self):
        """Stop the worker and wait for the thread to finish."""
        self._api_worker.stop()
        self.thread.quit()
        self.thread.wait()

    
    @pyqtSlot()
    def open_document(self, id):
        try:
            file_path = self._documents[id].save_filepath
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            os.startfile(file_path)
            self.docOpened.emit(id, None)
        except Exception as err:
            print(f"{traceback.format_exc()}: {err}")
            self.docOpened.emit(id, err)

    def _format_doc_status_name(self, id: str, status):
        try:
            document = self.documents[id]

            file_name = f"{document.file_name} " if document.file_name else ""
            pdf_base = os.path.basename(document.temp_doc_data.pdf_path).split(".")[0]
            pdf_name = pdf_base if file_name == "" else f"({self._truncate_string(pdf_base, 18)})"
            status = f"[{status}]:"
            name = f"{file_name}{pdf_name}"
            return status, name
        except Exception:
            print(traceback.format_exc())

    def _truncate_string(self, text: str, max_length: int, suffix="...") -> str:
        try:
            if len(text) > max_length:
                return text[:max_length - len(suffix)] + suffix
            return text
        except Exception:
            print(traceback.format_exc())

    def get_widget(self, id: str) -> CustomListItem | None:
        if id in self.doc_ui_map:
            _, widget = self.doc_ui_map[id]
            return widget

        return None