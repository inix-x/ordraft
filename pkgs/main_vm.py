import os
import sys
import traceback
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QEventLoop

if __name__ == "__main__" or "pkgs" not in sys.modules:
    test = sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    )
    print(test)


from pkgs.workers import AgentWorker, BackgroundWorker
from pkgs.models import CloudLLM, StateLLM
from pkgs.api import ModelLLM
from pkgs.placeholder_replacer import WordPlaceholderReplacer
from pkgs.dataclass import GenerateDocData, DocPayload, DocumentsCollection, Document, UpdateDocData
from pkgs.misc import Data
from pkgs.enums import TemplateFile, TemplateType
from pkgs.list_widget import CustomListItem


class MainViewModel(QObject):
    errorOccured = pyqtSignal(str)
    taskFinished = pyqtSignal(object)
    docGenerated = pyqtSignal()
    processing_finished = pyqtSignal(bool)
    updateDocStatus = pyqtSignal(Document)
    modelProcessed = pyqtSignal(Document)
    docEvents = pyqtSignal(Document)
    docOpened = pyqtSignal(str, object)

    chatbox_update = pyqtSignal(str)

    llm_stream_finished = pyqtSignal(bool)
    stream_stopped_sucess = pyqtSignal(bool)
    

    def __init__(self, data_model: Data = None):
        super().__init__()

        self._data_model = data_model
        self.word_processor = WordPlaceholderReplacer()

        self._documents = DocumentsCollection()
        self._document: Document = None
        self._doc_map = {}

        # Cloud LLMs
        self._cloud_llm = CloudLLM()
        self._local_llm = ModelLLM()
        
        # Agents
        self.setup_agents()

        
        # Connections
        self._cloud_llm.text_chunk.connect(self._update_chat_box)

        self._cloud_llm.error_occured.connect(self._cloud_llm_error)
        self._cloud_llm.stream_finished.connect(self._cloud_llm_stream_finished)
        self._cloud_llm.stream_stopped.connect(self._stream_stopped_success)
        
        self._llm_state: StateLLM = None
        
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
                doc_payload=doc_payload,
            )
            self.documents.add(document)
            self._document = document
            self.docEvents.emit(document)
            self.set_template(data.selected_template, data.is_reply_included)
        except Exception as ve:
            print(traceback.format_exc())
            self.errorOccured.emit(str(ve))
            return False, ve
            
        try:
            # self._api_worker.add_task(data=document)
            self._cloud_llm_worker.add_task(self._cloud_llm.assistant_message, data=document)
            return True, None
        except Exception as e:
            self.errorOccured.emit(str(e))
            return False, e
        
    def set_template(self, selected_template: TemplateType, is_reply_included: bool = False):
        try:
            if not isinstance(selected_template, TemplateType):
                raise TypeError("selected template is not a valid TemplateType")
            if selected_template is None:
                raise ValueError("Selected template is None")            
                
            template_file = TemplateFile.get_template_file(selected_template, is_reply_included)
            template_filepath = os.path.join(self._data_model.app_data_path, template_file)
            
            self.word_processor.template_filepath = template_filepath
        except Exception as e:
            print(traceback.format_exc())
            self.errorOccured.emit(str(e))

    def is_new_session(self, pdf_file_path) -> bool:
        try:
            if self._document is None:
                return True
                
            if pdf_file_path != self._document.temp_doc_data.pdf_path:
                return True

            return False
        except Exception:
            return True

    # -----Private-----
    def _handle_document_generation(self):
        try:
            # doc.validate()
            doc = self._document
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
            self._cloud_llm_worker.allow_next_task()
            # self._api_worker.allow_next_task()
            pass
    
    @pyqtSlot(str)
    def _update_chat_box(self, text_chunk):
        if text_chunk not in ["<think>", "</think>"]:
            self.chatbox_update.emit(text_chunk)
    
    @pyqtSlot(object)
    def _cloud_llm_error(self, err):
        self.errorOccured.emit(err)

    @pyqtSlot(bool, str)
    def _cloud_llm_stream_finished(self, state, output):
        success, parsed_output = self._cloud_llm._parse_response(output)
        
        if success:
            self._document.doc_payload.status = "Success"
            self._document.doc_payload.api_response = parsed_output
        
        self.llm_stream_finished.emit(state)
    
    @pyqtSlot(bool)
    def _stream_stopped_success(self, state):
        self.stream_stopped_sucess.emit(state)
    
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
        
    def setup_agents(self):
        
        # self._api_worker_thread = QThread()
        # self._api_worker = ApiWorker(ModelLLM())
        # self._api_worker.moveToThread(self._api_worker_thread)
        # self._api_worker.statusChanged.connect(self._handle_status_changed)
        # self._api_worker.finished.connect(self._api_worker_thread.quit)

        # self._api_worker_thread.started.connect(self._api_worker.run)
        # self._api_worker_thread.start()

        self._cloud_llm_worker_thread = QThread()
        self._cloud_llm_worker = AgentWorker()
        self._cloud_llm_worker.status_changed.connect(self._handle_status_changed) # not activated yet
        self._cloud_llm_worker.finished.connect(self._cloud_llm_worker_thread.quit)
        self._cloud_llm_worker.error_occured.connect(self._handle_error)
        self._cloud_llm_worker.moveToThread(self._cloud_llm_worker_thread)
        
        self._cloud_llm_worker_thread.started.connect(self._cloud_llm_worker.run)
        self._cloud_llm_worker_thread.start()

    def stop_agents(self):
        """Stop the worker and wait for the thread to finish."""
        # self._api_worker.stop()
        # self._api_worker_thread.quit()
        # self._api_worker_thread.wait()

        
        self._cloud_llm_worker.stop()
        self._cloud_llm_worker_thread.quit()

        event_loop = QEventLoop()
        self._cloud_llm_worker_thread.finished.connect(event_loop.quit)
        event_loop.exec()  # This keeps the UI responsive while waiting

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
    

    @pyqtSlot(object)
    def _handle_error(self, err: object):
        print(err)

    @pyqtSlot(bool)
    def handle_stream_stop(self, state):
        self._cloud_llm.stop()
