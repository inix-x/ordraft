import os
import sys
import traceback
from uuid import uuid4

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

if __name__ == "__main__" or "annogen" not in sys.modules:
    test = sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    )
    print(test)
    
from pkgs.api import ApiWorker, ModelLLM
from pkgs.placeholder_replacer import WordPlaceholderReplacer
from pkgs.types import GenerateDocData, DocPayload, DocumentsCollection, Document, UpdateDocData
from pkgs.misc import Data
from pkgs.enums import TemplateFile

class MainViewModel(QObject):
    errorOccured = pyqtSignal(str)
    taskFinished = pyqtSignal(object)
    docGenerated = pyqtSignal()
    processing_finished = pyqtSignal(bool)
    updateDocStatus = pyqtSignal(Document)
    docEvents = pyqtSignal(UpdateDocData)
    duplicateDetected = pyqtSignal(UpdateDocData)
    docOpened = pyqtSignal(object)

    def __init__(self, data_model: Data):
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
            uuid = uuid4()
            doc_payload = DocPayload(
                uuid=uuid,
                status="Queued",
                api_url=data.url,
                model=data.model
            )
            doc_payload.validate()
            document = Document(
                uuid=uuid,
                temp_doc_data=data,
                doc_payload=doc_payload
            )
            doc_status = UpdateDocData(
                uuid=uuid,
                status="Queued",
                name=os.path.basename(data.pdf_path)[0]
            )
            self.documents.add(document)

            self.docEvents.emit(doc_status)
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
    def _check_duplicate(self, data: GenerateDocData):
        if self.documents.len() == 0:
            return
        
        for _existing in self.documents:
            _existing: Document = _existing
            if _existing.temp_doc_data.pdf_path == data.pdf_path and \
                _existing.doc_payload.status == "Document Generated":
                doc_status = UpdateDocData(
                    uuid=_existing.uuid,
                    status="Duplicate",
                    name=_existing.file_name
                )
                self.duplicateDetected.emit(doc_status)

    # @pyqtSlot(DocPayload)
    # def draft_dismissal(self, api_data: DocPayload) -> bool:
    #     try:
    #         api_data.validate()
    #     except ValueError as ve:
    #         print(ve)
    #         return
    #     try:
    #         case_number: str = api_data.api_response.get("case_number")
    #         api_data.api_response["case_number_only"] = case_number[-9:]

    #         # print(api_data.api_response)

    #         document_data = self._documents[api_data.uuid]

    #         self.word_processor.replace_placeholders(api_data.api_response)
    #         doc_filepath = self.word_processor.save(document_data.temp_doc_data.save_path, case_number)
    #         document_data.file_name = f"{case_number}.docx"
    #         document_data.save_filepath = doc_filepath
    #         document_data.doc_payload.status = "Document Generated"
    #         # self._handle_status_changed(document_data.doc_payload)
    #     except Exception as e:
    #         document_data.doc_payload.status = "Error Occured"
    #         document_data.doc_payload.error_occured = e
    #         # self._handle_status_changed(document_data.doc_payload)
    #         return

    def _handle_document_generation(self, api_data: DocPayload):
        try:
            api_data.validate()
            document = self.documents[api_data.uuid]
            doc_status = UpdateDocData(
                uuid=document.uuid,
                status="Generating Document",
                name=document.file_name,
            )
            self.docEvents.emit(doc_status)
            document = self.word_processor.draft_dismissal(api_data, document)
            doc_status = UpdateDocData(
                uuid=document.uuid,
                status="Document Generated",
                name=document.file_name,
            )
            self.docEvents.emit(doc_status)
        except Exception as e:
            doc_status = UpdateDocData(
                uuid=document.uuid,
                status="Error Generating Document",
                name=document.file_name,
                error=e
            )
            self.docEvents.emit(doc_status)
        finally:
            self._api_worker.allow_next_task()

    def _duplicate(self, api_data: DocPayload):
        _running = self.documents[api_data.uuid]
        
        for _existing in self.documents:
            _existing: Document = _existing
            if _existing.temp_doc_data.pdf_path == _running.temp_doc_data.pdf_path and \
                _existing.doc_payload.status == "Document Generated":
                doc_status = UpdateDocData(
                    uuid=_existing.uuid,
                    status="Duplicate",
                    name=_existing.file_name
                )
                self.duplicateDetected.emit(doc_status)
            
    @pyqtSlot(DocPayload)
    def _handle_status_changed(self, api_data: DocPayload):
        try:
            document_data = self._documents[api_data.uuid]
            document_data.doc_payload = api_data
            self._documents[api_data.uuid] = document_data

            doc_status = UpdateDocData(
                uuid=document_data.uuid,
                status=document_data.doc_payload.status,
                name=document_data.file_name,
            )

            # self._duplicate(api_data)

            if api_data.error_occured:
                doc_status.error = api_data.error_occured
                self.docEvents.emit(doc_status)
                return

            if api_data.status == "Data Processed":
                self._handle_document_generation(api_data)
            else:
                self.docEvents.emit(doc_status)
        except Exception as e:
            print(e)
            return
        
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
    def open_document(self, uuid):
        e = None
        try:
            file_path = self._documents[uuid].save_filepath
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            os.startfile(file_path)
        except KeyError as err:
            print(f"Error: Document with UUID {uuid} not found in the collection.")
            e = err
        except FileNotFoundError as err:
            print(f"Error: {e}")
            e = err
        except OSError as err:
            print(f"OS Error: {e}")
            e = err
        finally:
            self.docOpened.emit(e)
            

    def _format_doc_status_name(self, uuid, status):
        try:
            document = self.documents[uuid]

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
