# fmt: off
import os
import sys
import pdf2image
import pytesseract
if sys.platform.startswith('win'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
elif sys.platform == 'darwin':
    if os.path.exists('/opt/homebrew/bin/tesseract'):
        pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'
    elif os.path.exists('/usr/local/bin/tesseract'):
        pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

import traceback
import json
import requests
import pdfplumber
import pikepdf
import re
import numpy as np
import io
from PIL import Image

from enum import Enum
from httpx import URL
from openai import OpenAI
from PyQt6.QtCore import (
    QObject, pyqtSignal
)

if __name__ == "__main__" or "pkgs" not in sys.modules:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pkgs.config import (
    DismissalGuidelines,
    RESO_DEFAULT_GUIDELINES,
    RESO_TEMPLATE,
    DISMISSAL_TEMPLATE,
    DEFAULT_INSTRUCTIONS,
    IMPORTANT_PROMPT,
    SYSTEM_PROMPT,
)
from pkgs.dataclass import Document
from pkgs.config import ORDRAFT_ADMIN, NOVITA_KEY
from pkgs.enums import TemplateType

# fmt: on

sys.setrecursionlimit(10000)

HEADERS = {"Content-Type": "application/json"}
__ENDPOINT_NAMESPACE__ = "inix-x"
__ENDPOINT_NAME__ = "deepseek-r1-distill-llama-8b-spg"
__ENDPOINT_NAME_V2__ = "ordraft-v1"
__API_URL__ = "https://api.endpoints.huggingface.cloud"


class StateLLM(Enum):
    Pending = "pending"
    Initializing = "initializing"
    Updating = "updating"
    Paused = "paused"
    Update_Failed = "updateFailed"
    Failed = "failed"
    SCALED_TO_ZERO = "scaledToZero"
    Running = "running"


class HuggingFaceAPI(QObject):
    llm_state_changed = pyqtSignal(StateLLM)
    error_occured = pyqtSignal(object)
    llm_state_checked = pyqtSignal(StateLLM)

    def __init__(self):
        super().__init__()
        self._endpoint =  __ENDPOINT_NAME_V2__
        self._namespace = __ENDPOINT_NAMESPACE__
        self._api_url: URL = __API_URL__

        self._headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {ORDRAFT_ADMIN}"
        }
        self._llm_endpoint = None
        self._llm_model = None
        self._llm_endpoint_state: StateLLM = None        

    @property
    def llm_state(self) -> StateLLM:
        if self._llm_endpoint_state is None:
            self._llm_endpoint_state = self.get_llm_state()

        return self._llm_endpoint_state

    @llm_state.setter
    def llm_state(self, state: StateLLM):
        if self._llm_endpoint_state != state and \
            isinstance(state, StateLLM):
            self._llm_endpoint_state = state
        
    @property
    def llm_endpoint(self):
        return self._llm_endpoint

    @llm_endpoint.setter
    def llm_endpoint(self, url: URL):
        if not isinstance(url, URL):
            raise TypeError(f"url is not type of {type(url)}, must be a valid url.")

        self._llm_endpoint = url

    @property
    def llm_model(self):
        return self._llm_model

    @llm_endpoint.setter
    def llm_endpoint(self, model: str):
        if not isinstance(model, str):
            raise TypeError("model is not a valid type")

        self._llm_endpoint = model

    def initialize(self):
        success, res = self._get_endpoint_information()

        if success is False:
            raise RuntimeError(f"Unable to initialize HuggingFaceAPI: {res}")

        status: dict = res.get("status")
        state: str = status.get("state")

        if state == "running":
            self.llm_endpoint = status.get("url")

    def get_llm_state(self) -> StateLLM:
        success, res = self._get_endpoint_information()

        if success is False:
            raise RuntimeError(f"Unable to get LLM State: {res}")

        status: dict = res.get("status")
        state: str = status.get("state")

        if state is None:
            raise ValueError("Missing 'state' key in status.")

        state_enum = None
        try:
            state_enum = StateLLM(state)
            self.llm_state_changed.emit(state_enum)
        except ValueError:
            self.error_occured.emit(ValueError(f"Invalid state: {state}"))
        finally:
            return state_enum

    def get_llm_endpoint(self) -> URL:
        success, res = self._get_endpoint_information()

        if success is False:
            raise RuntimeError(f"Unable to get LLM State: {res}")

        status: dict = res.get("status")
        url: str = status.get("url")

        if not isinstance(url, URL):
            raise TypeError("url provided not a valid")

        self.llm_endpoint = url

    def resume_llm_endpoint(self):
        res = {}
        success = True
        try:
            url = f"{self._api_url}/v2/endpoint/{self._namespace}/{self._endpoint}/resume"
            response = requests.post(url, headers=self._headers, timeout=300)
            response.raise_for_status()

            res = response.json()
        except requests.RequestException as e:
            print(f"Error occurred during API request: {e}")
            success = False
            res = e
        except Exception as e:
            print(f"Error occurred during API request: {e}")
            success = False
            res = e
        finally:
            return success, res

    def stop_llm_endpoint(self):
        res = {}
        success = True
        try:
            url = f"{self._api_url}/v2/endpoint/{self._namespace}/{self._endpoint}/pause"
            response = requests.post(url, headers=self._headers, timeout=300)
            response.raise_for_status()

            res = response.json()
        except requests.RequestException as e:
            print(f"Error occurred during API request: {e}")
            success = False
            res = e
        except Exception as e:
            print(f"Error occurred during API request: {e}")
            success = False
            res = e
        finally:
            return success, res

    def start_llm_service(self):
        if self.llm_state in [StateLLM.Running, 
            StateLLM.Pending, StateLLM.Updating]:
            self.llm_state_checked.emit(self.llm_state)
            return
        
        success, res = self.resume_llm_endpoint()

        if success is False:
            return success, res
        
        status:dict = res.get("status")
        state = status.get("state")

        if state not in StateLLM._value2member_map_:
            raise ValueError(f"State is not valid {state}")
            
        state_enum = StateLLM(state)
        self.llm_state = state_enum
        self.llm_state_changed.emit(state_enum)
        
        return success, res

    def stop_llm_service(self):
        if self.llm_state not in [StateLLM.Running, 
            StateLLM.Pending, StateLLM.Updating, StateLLM.Initializing]:
            self.llm_state_checked.emit(self.llm_state)
            return
        
        success, res = self.stop_llm_endpoint()

        if success is False:
            return success, res
        
        status:dict = res.get("status")
        state = status.get("state")

        if state not in StateLLM._value2member_map_:
            raise ValueError(f"State is not valid {state}")
            
        state_enum = StateLLM(state)
        self.llm_state = state_enum
        self.llm_state_changed.emit(state_enum)
        
        return success, res

    # -----Private-----
    def _get_endpoint_information(self) -> tuple[bool, dict]:
        """
        Sends a GET request to the API endpoint.

        Returns:
            dict: The JSON response from the API or None if the request fails.
        """
        
        res = {}
        success = True
        try:
            url = f"{self._api_url}/v2/endpoint/{self._namespace}/{self._endpoint}"
            response = requests.get(url, headers=self._headers, timeout=300)
            response.raise_for_status()

            res = response.json()
        except requests.RequestException as e:
            print(f"Error occurred during API request: {e}")
            success = False
            res = e
        except Exception as e:
            print(f"Error occurred during API request: {e}")
            success = False
            res = e
        finally:
            return success, res


class CloudLLM(QObject):
    stream_finished = pyqtSignal(bool, str)
    status_changed = pyqtSignal(Document)
    text_chunk = pyqtSignal(bool, str)
    extra_chat_update = pyqtSignal(str)
    error_occured = pyqtSignal(object)

    stream_start = pyqtSignal(bool)
    stream_stopped = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        # self._hugging_face_api = HuggingFaceAPI()
        # self._hugging_face_api.initialize()
        
        self._llm_client = OpenAI(
            base_url="https://api.novita.ai/v3/openai",
            api_key=NOVITA_KEY
            )
        
        
        self._api_key = self._llm_client.api_key
        self._model = None


        self._stop_requested = False
    def __post_init__(self):
        pass

    # @property
    # def hugging_face_api(self) -> HuggingFaceAPI:
    #     return self._hugging_face_api

    @property
    def url(self) -> URL:
        return self._llm_client.base_url

    @url.setter
    def url(self, url: URL):
        if not isinstance(url, URL):
            raise TypeError(f"url provided is type {type(url)}, must be url.")

        self._llm_client.base_url = url

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        if not isinstance(api_key, str):
            raise TypeError(f"API Key provided is type {type(api_key)}, must be str.")

        self._api_key = api_key

    def _create_prompt(self, role: str, prompt: str) -> dict:
        return {"role": role, "content": prompt}
    
    def flatten_pdf_in_memory(self, pdf_path):  
        try:  
            with pikepdf.open(pdf_path) as pdf:  
                output_buffer = io.BytesIO()  
                pdf.save(output_buffer)  
                output_buffer.seek(0)  
                return output_buffer  
        except Exception as e:  
            print(f"Error flattening PDF: {e}")  
            return None  
        
    def pdf_to_text(self, pdf_path, poppler_path=None):
        """
        Convert a PDF file to text using Tesseract OCR.

        :param pdf_path: Path to the PDF file.
        :param poppler_path: (Optional) Path to the Poppler bin directory (Windows only).
        :return: Extracted text from the PDF.
        """
        images = []
        try:
            if poppler_path and sys.platform.startswith('win'):
                images = pdf2image.convert_from_path(pdf_path, poppler_path=poppler_path)
            else:
                images = pdf2image.convert_from_path(pdf_path)
        except Exception as e:
            print(f"Error converting PDF: {e}")
            if sys.platform.startswith('win'):
                print("Attempting default Poppler path...")
                try:
                    default_poppler_path = r"C:\\Program Files (x86)\\Poppler\\poppler-24.08.0\\Library\\bin"
                    images = pdf2image.convert_from_path(pdf_path, poppler_path=default_poppler_path)
                except Exception as e2:
                    raise RuntimeError("Couldn't find Poppler; please install it, update the poppler_path, or disable the OCR") from e2
            elif sys.platform == 'darwin':
                print("Attempting default macOS Poppler paths...")
                mac_poppler_paths = [
                    "/opt/homebrew/bin",
                    "/usr/local/bin", 
                    "/opt/local/bin"  # MacPorts path
                ]
                success = False
                for mac_path in mac_poppler_paths:
                    try:
                        images = pdf2image.convert_from_path(pdf_path, poppler_path=mac_path)
                        success = True
                        break
                    except Exception:
                        continue
                
                if not success:
                    raise RuntimeError("Couldn't find Poppler on macOS. Please install it using 'brew install poppler' or 'port install poppler', or disable OCR.") from e
            else:
                raise RuntimeError("Error converting PDF to images. Please ensure Poppler is installed correctly for your system.") from e

        full_text = ""
        total_pages = len(images)
        for page_number, image in enumerate(images, start=1):
            self.extra_chat_update.emit(f"Scanning with OCR... {int(((page_number) / total_pages) * 100)}%\n")
            page_text = pytesseract.image_to_string(image)
            full_text += page_text + "\n"
        
        return full_text


    def _extract_text_from_pdf(self, pdf_path: str, ocr_enabled: bool = False):
        """
        Extracts text from the specified PDF file using pdfplumber.

        Returns:
            str: The extracted text or None if extraction fails.
        """
        text = ""
        try:
            if ocr_enabled is True:
                text = self.pdf_to_text(pdf_path)
            else:
                with pdfplumber.open(pdf_path) as pdf:
                    total_pages = len(pdf.pages)
                    for idx, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        self.extra_chat_update.emit(f"Reading... {int(((idx) / total_pages) * 100)}%\n")
                        if page_text:
                            text += page_text + "\n"
            return text if text.strip() else None
        except Exception as e:
            print(traceback.format_exc())
            return None
        
    def build_prompt(self, data: Document):
        try:
            pdf_text = self._extract_text_from_pdf(data.temp_doc_data.pdf_path, data.ocr_enable)

            if pdf_text is None:
                raise RuntimeError(f"Unable to extract text from the Document")
            
            guidelines = None
            template = None
            
            if data.temp_doc_data.selected_template in [TemplateType.RESO_AIR, 
                TemplateType.RESO_WATER, TemplateType.RESO_PD, TemplateType.RESO_HW]:
                guidelines = RESO_DEFAULT_GUIDELINES
                template = RESO_TEMPLATE
            # elif data.temp_doc_data.selected_template in [TemplateType.PENALTY_PD, 
            #     TemplateType.DISMISSAL_WATER, TemplateType.PENALTY_AIR, TemplateType.PENALTY_HW]:
            #     guidelines = RESO_DEFAULT_GUIDELINES
            #     template = DISMISSAL_TEMPLATE
            else:
                base_guideline = DismissalGuidelines()
                base_guideline.document_type = data.temp_doc_data.selected_template
                guidelines = base_guideline.guidelines
                template = DISMISSAL_TEMPLATE

            user_prompt = f"""
            **TASK**  
            Please extract the following information from the text labeled as PDF_TEXT and fill in the JSON template exactly as shown below.

            {DEFAULT_INSTRUCTIONS}
            {IMPORTANT_PROMPT}
            {guidelines}
            
            **TEMPLATE (DO NOT MODIFY THE KEYS)**
            Template:
            {template}

            PDF_TEXT:
            {pdf_text}
            """
            return user_prompt
        except Exception as e:
            return e

    def assistant_message(self, document: Document):
        try:
            user_prompt_text = self.build_prompt(document)
            if isinstance(user_prompt_text, Exception):
                raise RuntimeError(str(user_prompt_text))
            user_prompt = self._create_prompt("user", user_prompt_text)
            system_prompt = self._create_prompt("system", SYSTEM_PROMPT)
        except Exception as prompt_error:
            self.stream_finished.emit(True, None)
            self.error_occured.emit(str(prompt_error))
            return 
        
        self.extra_chat_update.emit("\nI will now start analyzing the document\n")
        buffer: str = ""
        current_think_text: str = ""  
        
        self._stop_requested = False
        try:
            self.stream_start.emit(True)
            chat_completion = self._llm_client.chat.completions.create(
                model="deepseek/deepseek-r1-distill-llama-70b",
                messages=[user_prompt, system_prompt],
                temperature=0.77,
                max_tokens=8192,
                stream=True,
                timeout=10
            )

            for message in chat_completion:
                if self._stop_requested is True:
                    self.stream_stopped.emit(True)
                    break

                try:
                    text = message.choices[0].delta.content
                except Exception as e:
                    print(f"Error extracting text chunk: {e}")
                    continue

                if text:
                    buffer += text

                    start_idx = buffer.find("<think>")
                    if start_idx != -1:
                        start_idx += len("<think>")
                        end_idx = buffer.find("</think>", start_idx)

                        if end_idx == -1:
                            new_text = buffer[start_idx:]
                        else:
                            new_text = buffer[start_idx:end_idx]

                        if new_text.startswith(current_think_text):
                            delta = new_text[len(current_think_text):]
                            if delta:
                                self.text_chunk.emit(True, delta)
                                current_think_text += delta
                        else:
                            self.text_chunk.emit(True, new_text)
                            current_think_text = new_text

                        if end_idx != -1:
                            buffer = buffer[end_idx + len("</think>"):]
                            current_think_text = ""
                            self.text_chunk.emit(False, "")

        except Exception as e:
            self.error_occured.emit(f"\n[Error] {str(e)}")
        finally:
            completed = not self._stop_requested
            self.stream_finished.emit(completed, buffer)

    def stop(self):
        """Call this method to stop the streaming process."""
        self._stop_requested = True


    def _parse_response(self, content) -> tuple[bool, dict]:
        """
        Parses the API response to extract the JSON block with the structured information.

        Parameters:
            content (str):

        Returns:
            dict: The extracted structured information or None if parsing fails.
        """

        json_string_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
        if json_string_match:
            json_string = json_string_match.group(1)
            try:
                processed = json_string.replace("\n", "")
                result = json.loads(processed)

                if not isinstance(result, (dict, json)):
                    raise TypeError(f"Not a valid response: response is {type(result)}")
                
                return True, result
            except json.JSONDecodeError as e:
                res = {"message": f"Error decoding JSON: {e}"}
                return False, res
        else:
            return False, {"message": "JSON block not found in the response."}
        
if __name__ == "__main__":
    test = CloudLLM()
    text = test._extract_text_from_pdf("C:\\Users\\omarg\\Downloads\\WR WATER - R.V.R. MACHINE SHOP.pdf")
    print(text)