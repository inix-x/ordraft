import json
import requests
import pdfplumber
import re
import queue

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QWaitCondition, QMutex

from .config import DEFAULT_GUIDELINES, DEFAULT_INSTRUCTIONS
from .types import DocPayload, Document


class ModelLLM(QObject):
    data_received = pyqtSignal(dict)
    statusChanged = pyqtSignal(DocPayload)

    def __init__(
        self,
        api_url="http://localhost:1234",
        model="deepseek-r1-distill-qwen-7b",
    ):
        super().__init__()  

        self._pdf_path = None 
        self.api_url = api_url
        self.model = model       

    @property
    def pdf_path(self):
        return self._pdf_path

    @pdf_path.setter
    def pdf_path(self, path):
        self._pdf_path = path

    def start(self, data: Document):
        pdf_path = data.temp_doc_data.pdf_path
        data.doc_payload.status = "Preparing PDF"
        self.statusChanged.emit(data.doc_payload)

        pdf_text = self._extract_text_from_pdf(pdf_path)
        payload = self._build_payload(
            pdf_text=pdf_text, custom_prompt=data.temp_doc_data.custom_prompt
        )

        data.doc_payload.status = "Extracting Data w/ AI"
        self.statusChanged.emit(data.doc_payload)
        success, res = self._send_request(
            payload=payload,
            url=data.doc_payload.api_url
        )
        if success is False:
            data.doc_payload.status = "API Error"
            data.doc_payload.error_occured = res
            self.statusChanged.emit(data.doc_payload)
            return 

        data.doc_payload.status = "Data Received"
        self.statusChanged.emit(data.doc_payload)


        valid_data, res = self._parse_response(res)
        if valid_data is False:
            self._handle_error(data=data, res=res)
        
        data.doc_payload.status = "Data Processed"
        data.doc_payload.api_response = res
        self.statusChanged.emit(data.doc_payload)

    # -----Private------
    def _handle_error(self, data: Document, res: object):
        data.doc_payload.status = "Invalid Response"
        data.doc_payload.api_response = res
        self.statusChanged.emit(data.doc_payload)

    def _send_request(
            self, 
            payload, 
            url
            # port
        ) -> tuple[bool, object]:
        """
        Sends a POST request to the API endpoint with the given payload.

        Parameters:
            payload (dict): The payload to send.

        Returns:
            dict: The JSON response from the API or None if the request fails.
        """
        headers = {"Content-Type": "application/json"}
        res = {}
        succeess = True
        try:
            this_url = f"{url}/v1/chat/completions"

            response = requests.post(this_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()  
            res = response.json()
        except requests.RequestException as e:
            print(f"Error occurred during API request: {e}")
            succeess = False
            res = e
        finally:
            return succeess, res

    def _extract_text_from_pdf(self, pdf_path: str):
        """
        Extracts text from the specified PDF file using pdfplumber.

        Returns:
            str: The extracted text or None if extraction fails.
        """
        text = ""
        try:
            # new: Open the PDF file using pdfplumber in a context manager
            with pdfplumber.open(pdf_path) as pdf:
                # new: Iterate over each page and extract text
                for page in pdf.pages: 
                    page_text = page.extract_text() 
                    if page_text:
                        text += page_text + "\n" 
            return text
        except Exception as e:
            print(f"Error occurred while extracting text: {e}")  
            return None

    def _build_payload(self, custom_prompt: str, pdf_text: str):
        """
        Constructs the payload to be sent to the API for extracting structured information.

        Parameters:
            pdf_text (str): The extracted text from the PDF.

        Returns:
            dict: The JSON payload.
        """
        # new: Define the JSON template for the extracted information
        template = '''
        {
            "client_name": "",
            "location": "",
            "case_number": "",
            "date_of_inspection": "",
            "violations": [
                "",
                "",
                ""
            ]
            }
        }
        '''
        prompt = custom_prompt if custom_prompt else DEFAULT_GUIDELINES

        prompt = f'''
            {prompt}

            {DEFAULT_INSTRUCTIONS}
        '''
        # new: Build the user prompt by embedding the template and guidelines along with the PDF text.
        user_prompt = f"""
            **TASK**  
            Please extract the following information from the text labeled as PDF_TEXT and fill in the JSON template exactly as shown below.

            {prompt}
            
            **TEMPLATE (DO NOT MODIFY THE KEYS)**
            Template:
            {template}

            PDF_TEXT:
            {pdf_text}
        """
        # new: Construct the payload with the defined model and prompt
        payload = {
            "model": self.model,  
            "messages": [         
                {"role": "system", "content": "You are an assistant that extracts structured information from text."},  
                {"role": "user", "content": user_prompt}  
            ],
            "temperature": 0.7,  
            "max_tokens": -1,    
            "stream": False      
        }
        return payload

    def _parse_response(self, response_json) -> tuple[bool, dict]:
        """
        Parses the API response to extract the JSON block with the structured information.

        Parameters:
            response_json (dict): The JSON response from the API.

        Returns:
            dict: The extracted structured information or None if parsing fails.
        """
        if response_json is None:
            return False, {"message": "Empty"}
        choices = response_json.get("choices", [])
        if not choices:
            res = {"message":"No valid API Response found"}
            return False, res 

        message = choices[0].get("message", {})  
        content = message.get("content", "")     

        json_string_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)  
        if json_string_match:
            json_string = json_string_match.group(1)  
            try: 
                processed = json_string.replace("\n", "")
                result = json.loads(processed)  
                return True, result  
            except json.JSONDecodeError as e:
                res = {"message": f"Error decoding JSON: {e}"}
                return False, res
        else:
            return False, {"message": "JSON block not found in the response."}

class ApiWorker(QObject):
    statusChanged = pyqtSignal(DocPayload)
    finished = pyqtSignal(bool)

    def __init__(self, llm_model: ModelLLM):
        super().__init__()

        # Private Data
        self._task_queue = queue.Queue()
        self._running = True

        # ---- Control for processing tasks ----
        # When _processing_allowed is False, the worker will wait before processing the next task.
        self._processing_allowed = False
        self._mutex = QMutex()
        self._condition = QWaitCondition()

        # Model
        self._llm_model = llm_model

        # Signals
        self._llm_model.statusChanged.connect(self._handle_events)

    # -----Public API-----
    def add_task(self, data: DocPayload):
        """Called to add a new task to the queue."""
        
        was_empty = self._task_queue.empty()
        self._task_queue.put(data)
        if was_empty:
            self._auto_unlock()


    def stop(self):
        """Called to stop the worker loop."""
        self._running = False

    def run(self):
        """This method runs in a separate thread and waits for tasks indefinitely."""
        print("AI Agent Running")
        while self._running:
            try:
                task_data = self._task_queue.get(timeout=1)
            except queue.Empty:
                continue

            self._mutex.lock()
            while not self._processing_allowed:
                self._condition.wait(self._mutex)
            self._processing_allowed = False
            self._mutex.unlock()

            self._llm_model.start(task_data)
            self._task_queue.task_done()

        print("AI Agent Stopping")
        self.finished.emit(True)

    @pyqtSlot()
    def allow_next_task(self):
        """Call this slot to allow processing of the next queued task."""
        if self._processing_allowed is False:    
            self._mutex.lock()
            self._processing_allowed = True
            self._condition.wakeOne()
            self._mutex.unlock()

    # -----Private API-----
    @pyqtSlot(DocPayload)
    def _handle_events(self, data: DocPayload):
        self.statusChanged.emit(data)

    @pyqtSlot()
    def _auto_unlock(self):
        """Automatically unlock processing if the queue was empty and a new task is added."""
        self._mutex.lock()
        if not self._processing_allowed:
            self._processing_allowed = True
            self._condition.wakeOne()
        self._mutex.unlock()


if __name__ == '__main__':
    pdf_path = "C:\\Users\\omarg\\Downloads\\NOV_CASE.pdf"  
    api_url = "http://localhost:1234/v1/chat/completions"     
    or_draft = ModelLLM()           
    or_draft.pdf_path = pdf_path
    result = or_draft.extract_information()                
    print(result)  
