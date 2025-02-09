DEFAULT_GUIDELINES = '''**GUIDELINES**  
1. ENCLOSE your final output in a single code block (e.g., triple backticks ```json ... ```).  
2. The keys in the template must not be changed or rearranged.  
3. Fill the values with data extracted from the PDF_TEXT.  
4. `case_number` should always begin with `NOV-EMB-NCR`.  
5. `location` is the address of the establishment or the recipient.  
6. `client_name` is found immediately before `location` (may include a personal name and/or a company name).  
7. `violations`:  
- Identify the findings in the PDF_TEXT that pertain to violations.  
- **Rephrase** each violation in a clear, formal, legally appropriate style while preserving its meaning.  
- Do not omit critical information.  
8. If a particular field (e.g., date_of_inspection) is not present in the PDF_TEXT, leave it as an empty string.  
9. Ignore the following terms for location if they appear in the PDF_TEXT:  
- "National capital region"   
- "Philippines"  
- "National Capital Region EMB-NCR Bldg. National Ecology Center Compound, East Ave., Diliman, Quezon City"  
- "EMB-NCR Bldg. National Ecology Center Compound, East Ave., Diliman, Quezon City"  
'''
DEFAULT_INSTRUCTIONS = '''**INSTRUCTIONS**  
1. Carefully read the entire PDF_TEXT.  
2. Identify and extract the required details according to the template keys.  
3. Once extracted, place them into the template in the correct fields without adding any extra keys.  
4. Output only the completed JSON in a code block, without any explanations or additional text outside of it.
'''