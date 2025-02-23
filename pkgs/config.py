from dataclasses import dataclass
from .enums import TemplateType

IMPORTANT_PROMPT='''**GUIDELINES**
1. ENCLOSE your final output in a single code block (e.g., triple backticks ```json ... ```).  
2. The keys in the template must not be changed or rearranged.  
3. Fill the values with data extracted from the PDF_TEXT.  
'''

@dataclass
class DismissalGuidelines:
   document_type = TemplateType
   _base_template = '''
   Your task is to extract structured information from PDF text and map it to the following JSON template:

   1. **Temporal Extraction Node (Notice vs. Inspection Dates):**
      - **For `date_of_notice_of_violation`:**
         - **Primary Extraction:** Locate paragraph containing the phrase **"Notice is hereby served upon you"** the date immediately inside this paragraph.
         - **Additional Clue:** Also search for a phrase **"ACTS CONSTITUTING THE VIOLATION"**. If found, extract the date associated with that paragraph.
      - **For `date_of_inspection`:**
         - **Primary Extraction:** Locate the date before both the client name and location.
         - **Additional Clue:** There are times date of inspection is not indicated.
         - If a clear date isn't identified, default to the placeholder `"date_of_inspection"`.
         - This date is not in any paragraph.
      - **Fallback & Disambiguation:** 
         - If only one date is present, do not assign it to both date fields.
         - If both dates are the same, then check the guidelines again for date of notice of violation.
      - **date formatting:**
         - always format the date as dd month yyyy or 01 January 2025

   2. **Pattern Matching Node:**
      - Extract the `case_number` ensuring it starts with the prefix `"NOV-EMB-NCR"`.
      - Validate that the extracted string strictly begins with this prefix.

   3. **Entity and Address Recognition Node:**
      - Identify and extract the complete address for `location`.
      - Extract `client_name` as the text immediately preceding the location, which may include a personal or company name.

   4. **Section Parsing Node:**
      - Locate the section under the header **"ACTS CONSTITUTING THE VIOLATION"**.
      - **Strictly filter**: Extract text related and/or contains the following: <TEMPLATE_TYPE>.

   5. **Fallback and Error Handling Node:**
      - If any field (e.g., `date_of_inspection` or `date_of_notice_of_violation`) is not detected in the PDF text, use the corresponding field name as its value.
   '''

   @property
   def guidelines(self) -> str:

      if not self.document_type:
         raise ValueError("Document type must be provided")
      if not isinstance(self.document_type, TemplateType):
         raise TypeError("Document type must be a type of TemplatType")
      
      findings = None
      if self.document_type == TemplateType.DISMISSAL_AIR:
         findings = "findings related to air"
      if self.document_type == TemplateType.DISMISSAL_HW:
         findings = "findings related to HW (hazard/hazardous wastes)"
      if self.document_type == TemplateType.DISMISSAL_WATER:
         findings = "findings related to water"
      if self.document_type == TemplateType.DISMISSAL_PD:
         findings = "findings related to PD orADVANCE MARKETING Presidential Decree"


      final_prompt = self._base_template.replace("<TEMPLATE_TYPE>", findings)

      return final_prompt

RESO_DEFAULT_GUIDELINES = '''
0. **If a particular field (e.g., date_of_motion_for_recon) is not present in the PDF_TEXT, use the name of field as its value.**
1. `case_number` should always begin with `NOV-EMB-NCR`.  
2. `location` is the complete address of the establishment or the client.  
3. `client_name` is found immediately before `location` (may include a personal name and/or a company name).  
4. `decision_from_order`:  
- **STRICTLY** Copy the decision that can be found starting from 'WHEREFORE' and stop just before 'SO ORDERED.
- if the decision from order has '.', add \\t\\n\\n between after '.'.
5. `date_of_motion_for_recon`: this can be found on paragraph containing 'Respondent submitted its Position Paper'.
6. 'date_of_order' is found after the wherefore or before the signing section of regional director.
7 **date formatting:**
   - always format the date as dd month yyyy or 01 January 2025
'''
DEFAULT_INSTRUCTIONS = '''**INSTRUCTIONS**  
1. Carefully read the entire PDF_TEXT.  
2. Identify and extract the required details according to the template keys.  
3. Once extracted, place them into the template in the correct fields without adding any extra keys.  
4. Output only the completed JSON in a code block, without any explanations or additional text outside of it.
'''
SYSTEM_PROMPT ='''You are a professional-level legal assistant optimized for high-performance reasoning and clarity. Your task is to analyze the provided PDF_TEXT and generate a structured JSON output as specified. When processing this request, use only the minimal necessary internal reasoning and do not expose any internal chain-of-thought in your final output.

**Instructions:**

1. **Objective:**  
   - Analyze and interpret the provided **PDF_TEXT**.  
   - Extract all relevant details needed to populate specific fields in the JSON output as defined by the user.

2. **Data Extraction Rules:**  
   - **Extract and/or copy data**  
   - **Do not omit any law, rules, RA, or constitution.**  
   - **Ignore** the following text if it appears in the PDF_TEXT:  
     ```
     "National capital region",
     "National Capital Region EMB-NCR Bldg. National Ecology Center Compound, East Ave., Diliman, Quezon City",
     "EMB-NCR Bldg. National Ecology Center Compound, East Ave., Diliman, Quezon City"
     ```  
   - All other content in the PDF_TEXT is eligible for extraction and analysis.

3. **Priority of Instructions:**  
   - Always follow this system prompt as the top priority.  
   - Adhere to any additional user instructions provided, as long as they do not conflict with this prompt.

4. **Efficiency and Clarity:**  
   - Process the request with only the minimal internal reasoning necessary to generate a correct final output.  
   - Keep your internal chain-of-thought hidden and present only the concise, direct final answer.

'''

@dataclass
class FormatPromptTemplate:
   json_data: str
   phrases: str
   base_template: str = '''
   Preserve the original JSON structure and key-value pairs. Given the JSON below:

   ```json
   <INSERT_JSON_HERE>
   ```
   For each occurrence of the specified word or phrase(s) in the JSON values, locate the word or phrase(s) defined by <INSERT_PHRASES_HERE> and enclose them in markdown bold formatting (i.e., convert each to word/phrase). Do not modify any other parts of the JSON.
   Return the updated JSON with the changes applied.
   '''

   @property
   def prompt(self) -> str:
      """
      Generates the final prompt by replacing placeholders with provided JSON data and phrases.
      """
      if not self.json_data or not self.phrases:
         raise ValueError("Both 'json_data' and 'phrases' must be provided.")
      
      # new: Replace the placeholders in the base template
      final_prompt = self.base_template.replace("<INSERT_JSON_HERE>", self.json_data)
      final_prompt = final_prompt.replace("<INSERT_PHRASES_HERE>", self.phrases)
      return final_prompt


URL="http://127.0.0.1:1234"
ORDRAFT_USER = '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'
ORDRAFT_ADMIN = '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'

DISMISSAL_TEMPLATE = """{
    "date_of_notice_of_violation": "",
    "client_name": "",
    "location": "",
    "case_number": "",
    "date_of_inspection": "",
    "findings": [
        "",
        "",
        ""
    ]
}
"""

RESO_TEMPLATE = '''{
    "client_name": "",
    "location": "",
    "case_number": "",
    "date_of_order": "",
    "decision_from_order": "",
    "date_of_motion_for_recon": "",
}
'''


NOVITA_KEY= 'sk_DyKz7flavRxAMZ9MP1aF2oLj-w_cP8JuG0IGTH9Nu7s'
NOVITA = '39fffc5dbcd016b8573aed134dd96752efa5bce6b7d69a146e3206b0c426d0d4'