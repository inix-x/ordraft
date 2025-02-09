import json
import requests
import pdfplumber
import re

from PyQt6.QtCore import QThread, QThreadPool, QObject, pyqtSignal

from .config import DEFAULT_GUIDELINES, DEFAULT_INSTRUCTIONS

class RequestThread(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, payload, url, port, parent=None):
        super().__init__(parent)
        self.payload = payload
        self.url = url
        self.port = port
        self.response_json = None

    def run(self):
        """
        Runs the request in a separate thread. The response is stored
        in self.response_json, then the finishedSignal is emitted.
        """
        try:
            self._send_request(self.payload, self.url, self.port)
        except Exception as e:
            print(f"Request failed: {e}")
            self.response_json = None

    def _send_request(self, payload, url, port):
        """
        Sends a POST request to the API endpoint with the given payload.

        Parameters:
            payload (dict): The payload to send.

        Returns:
            dict: The JSON response from the API or None if the request fails.
        """
        headers = {"Content-Type": "application/json"}
        res = {}
        try:
            # Remove any leading/trailing spaces from the URL and port
            url = url.strip() if url else ""
            port = str(port).strip() if port else ""

            # Build the full URL with port if available
            url_port = f"{url}:{port}" if port else url

            # Ensure the URL doesn't have unwanted spaces
            this_url = f"{url_port}/v1/chat/completions" if url_port else url

            response = requests.post(this_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()  # Raise an error for bad HTTP responses
            res = response.json()  # Return JSON response
        except requests.RequestException as e:
            # Log any errors that occur
            print(f"Error occurred during API request: {e}")
        finally:
            self.finished.emit(res)
            return res

class OrDraft(QObject):
    data_received = pyqtSignal(dict)

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

    def extract_text_from_pdf(self):
        """
        Extracts text from the specified PDF file using pdfplumber.

        Returns:
            str: The extracted text or None if extraction fails.
        """
        text = ""
        try:
            # new: Open the PDF file using pdfplumber in a context manager
            with pdfplumber.open(self.pdf_path) as pdf:
                # new: Iterate over each page and extract text
                for page in pdf.pages: 
                    page_text = page.extract_text() 
                    if page_text:
                        text += page_text + "\n" 
            return text
        except Exception as e:
            print(f"Error occurred while extracting text: {e}")  
            return None

    def build_payload(self, custom_prompt: str, pdf_text: str):
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


    def parse_response(self, response_json):
        """
        Parses the API response to extract the JSON block with the structured information.

        Parameters:
            response_json (dict): The JSON response from the API.

        Returns:
            dict: The extracted structured information or None if parsing fails.
        """
        if response_json is None:
            return None
        choices = response_json.get("choices", [])  # new
        if not choices:
            print("No choices found in the response.")  # new
            return None

        message = choices[0].get("message", {})  
        content = message.get("content", "")     
        
        json_string_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)  
        if json_string_match:
            json_string = json_string_match.group(1)  
            try: 
                processed = json_string.replace("\n", "")
                result = json.loads(processed)  
                return result  
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")  
                return None
        else:
            print("JSON block not found in the response.")  
            return None

    def extract_information(self, url, port, custom_prompt=None):
        """
        High-level method to extract information from the PDF and retrieve structured data via the API.

        Returns:
            dict: The extracted structured information or None if any step fails.
        """
        pdf_text = self.extract_text_from_pdf()  
        if not pdf_text:
            print("Failed to extract text from PDF.")  
            return None
        
        payload = self.build_payload(pdf_text=pdf_text, custom_prompt=custom_prompt)  

        _url = self.api_url if url is None or len(url) == 0 else url
        _port= None if port is None or len(port) == 0 else port

        self.thread = QThread(self)  
        self.request_thread = RequestThread(payload=payload, url=_url, port=_port)
        self.request_thread.finished.connect(self.handle_finished)
        self.request_thread.start()

    def handle_finished(self, response_json):
        """
        Callback to handle the thread's finished signal.
        """
        if response_json is None or len(response_json) == 0:
            print("Failed to receive valid response.")
            self.data_received.emit({})
            return
        parsed = self.parse_response(response_json)
        self.data_received.emit(parsed)

if __name__ == '__main__':
    pdf_path = "C:\\Users\\omarg\\Downloads\\NOV_CASE.pdf"  
    api_url = "http://localhost:1234/v1/chat/completions"     
    or_draft = OrDraft()           
    or_draft.pdf_path = pdf_path
    result = or_draft.extract_information()                
    print(result)  
