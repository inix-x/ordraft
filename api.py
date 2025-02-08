import json
import requests
import pdfplumber
import re

class OrDraft:

    def __init__(
        self,
        api_url="http://localhost:1234/v1/chat/completions",
        model="deepseek-r1-distill-qwen-7b",
    ):
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

    def build_payload(self, pdf_text):
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

        # new: Build the user prompt by embedding the template and guidelines along with the PDF text.
        user_prompt = f"""
            Extract information from the provided PDF_TEXT and fill in the Template accordingly.

            Template:
            {template}

            Guidelines:
            - IMPORTANT: enclose the output, that is the json, in a codeblock for easy access.
            - STRICTLY FOLLOW THE TEMPLATE keys, DO NOT MODIFY THE KEYS IN TEMPLATE.
            - Extract information in the PDF file.
            - "case_number": always starts with NOV-EMB-NCR
            - "location": is the address of the establishment or the recipient.
            - "client_name": will always be before the location; sometimes the name of a person is accompanied by the name of an establishment or company.
            - "violations": COPY ONLY the findings and DO NOT generate, DO NOT add extra phrasing, DO NOT DEFINE.
            - Note: Ignore these terms: ["National capital region", "Philippines", "National Capital Region EMB-NCR Bldg. National Ecology Center Compound, East Ave., Diliman, Quezon City"]

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

    def send_request(self, payload):
        """
        Sends a POST request to the API endpoint with the given payload.

        Parameters:
            payload (dict): The payload to send.

        Returns:
            dict: The JSON response from the API or None if the request fails.
        """
        headers = {"Content-Type": "application/json"}  # new
        try:
            # new: Send the request to the API endpoint
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))  # new
            response.raise_for_status()  # new: Raise an error for bad HTTP responses
            return response.json()  # new
        except requests.RequestException as e:
            # new: Log errors related to the HTTP request
            print(f"Error occurred during API request: {e}")  # new
            return None

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

    def extract_information(self):
        """
        High-level method to extract information from the PDF and retrieve structured data via the API.

        Returns:
            dict: The extracted structured information or None if any step fails.
        """
        pdf_text = self.extract_text_from_pdf()  
        if not pdf_text:
            print("Failed to extract text from PDF.")  
            return None

        payload = self.build_payload(pdf_text)  
        response_json = self.send_request(payload)  
        return self.parse_response(response_json)  

if __name__ == '__main__':
    pdf_path = "C:\\Users\\omarg\\Downloads\\NOV_CASE.pdf"  
    api_url = "http://localhost:1234/v1/chat/completions"     
    or_draft = OrDraft()           
    or_draft.pdf_path = pdf_path
    result = or_draft.extract_information()                
    print(result)  
