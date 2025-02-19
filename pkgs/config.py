IMPORTANT_PROMPT='''**GUIDELINES**
1. ENCLOSE your final output in a single code block (e.g., triple backticks ```json ... ```).  
2. The keys in the template must not be changed or rearranged.  
3. Fill the values with data extracted from the PDF_TEXT.  
'''
DISMISSAL_DEFAULT_GUIDELINES = '''
1. `case_number` should always begin with `NOV-EMB-NCR`.  
2. `location` is the complete address of the establishment or the recipient.  
3. `client_name` is found immediately before `location` (may include a personal name and/or a company name).  
4. `violations`:  
- list the findings in the PDF_TEXT that pertain to violations.  
- do not include the rule, section, laws, or penalty, only the findings from the acts consituting the violation.  
- add "." at the end of each findings identified.
- Be brief, and precise with the findings that will be placed on 'violations'.
5. `date_of_inspection` is always found immediately before violations.
6. If a particular field (e.g., date_of_inspection) is not present in the PDF_TEXT, leave it as an empty string.  
'''
RESO_DEFAULT_GUIDELINES = '''
0. **If a particular field (e.g., date_of_motion_for_recon) is not present in the PDF_TEXT, use the name of field as its value.**
1. `case_number` should always begin with `NOV-EMB-NCR`.  
2. `location` is the complete address of the establishment or the client.  
3. `client_name` is found immediately before `location` (may include a personal name and/or a company name).  
4. `decision_from_order`:  
- **STRICTLY** Copy the decision that can be found starting from WHEREFORE,
- This can be a 2 paragraph or just one.
5. `date_of_motion_for_recon`: this can be found on paragraph containing 'Respondent submitted its Position Paper'.
6. 'date_of_order' is found after the wherefore or before the signing section of regional director.
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
   - **Extract and/or copy only the findings and/or cause of violations.**  
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

URL="http://127.0.0.1:1234"
ORDRAFT_USER = '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'
ORDRAFT_ADMIN = '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'

DISMISSAL_TEMPLATE = """{
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