from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage


stream = True
client = OpenAI(
		base_url = "https://qlzg2fku4wsq4a7t.us-east-1.aws.endpoints.huggingface.cloud/v1/",
		api_key = "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"
	)

chat_completion: ChatCompletion = client.chat.completions.create(
	model="lmstudio-community/DeepSeek-R1-Distill-Llama-8B-GGUF",
	messages=[
	{
		"role": "user",
		"content": """**TASK**\nPlease extract the following information from the text labeled as PDF_TEXT and fill in the JSON template exactly as shown below.\n\n            \n            **GUIDELINES**  \n1. ENCLOSE your final output in a single code block (e.g., triple backticks ```json ... ```).  \n2. The keys in the template must not be changed or rearranged.  \n3. Fill the values with data extracted from the PDF_TEXT.  \n4. `case_number` should always begin with `NOV-EMB-NCR`.  \n5. `location` is the address of the establishment or the recipient.  \n6. `client_name` is found immediately before `location` (may include a personal name and/or a company name).  \n7. `violations`:  \n- list the findings in the PDF_TEXT that pertain to violations.  \n- do not include the rule, section, laws, or penalty, only the findings from the acts consituting the violation.  \n- add \".\" at the end of each findings identified.\n8. `date_of_inspection` is always found immediately before violations.\n9. If a particular field (e.g., date_of_inspection) is not present in the PDF_TEXT, leave it as an empty string.  \n\n\n            **INSTRUCTIONS**  \n1. Carefully read the entire PDF_TEXT.  \n2. Identify and extract the required details according to the template keys.  \n3. Once extracted, place them into the template in the correct fields without adding any extra keys.  \n4. Output only the completed JSON in a code block, without any explanations or additional text outside of it.\n\n        \n            \n            **TEMPLATE (DO NOT MODIFY THE KEYS)**\n            Template:\n            \n        {\n            \"client_name\": \"\",\n            \"location\": \"\",\n            \"case_number\": \"\",\n            \"date_of_inspection\": \"\",\n            \"violations\": [\n                \"\",\n                \"\",\n                \"\"\n            ]\n            }\n        }\n        \n\n            PDF_TEXT:\n            Republic of the Philippines\nDepartment of Environment and Natural Resources\nENVIRONMENTAL MANAGEMENT BUREAU\nNATIONAL CAPITAL REGION\nEMB-NCR Bldg. National Ecology Center Compound, East Ave., Diliman, Quezon City\nE-mail: recordsncr@emb.gov.ph | ncrsupport@emb.gov.ph\nTel.#: 8931-1331 local: | CPD:1110-1113 | EMED:1118-1124 | FAD:1103-1107 | ORD:1114-1117 |\nThe President/General Manager\nLINKTEX INDUSTRIAL CORPORATION\n64 Victoneta Avenue,\nPotrero, Malabon City\nSUBJECT : NOTICE OF VIOLATION\nNOV-EMB-NCR-2022-0043\nSir/Madam:\nNotice is hereby served upon you for having violated the provisions of (RA 6969) known as the Toxic\nand Hazardous Substances and Nuclear Wastes Control Act of 1990 and (RA 9275) known as the\nPhilippine Clean Water Act of 2004, as found during the inspection conducted by the technical\npersonnel of this Office on 16 November 2021.\nACTS CONSTITUTING THE VIOLATION\nFINDINGS PROHIBITED ACTS\nFor failure to register as a hazardous waste Chapter 3.3 of the DENR Administrative Order (DAO)\ngenerator considering the Respondent is 2013-22, Revised Procedure and Standards for the\npossible to generate hazardous waste such Management of Hazardous Wastes.1\nas but not limited to LED lights and waste\nelectronic and electrical equipment (M506) “Waste generator” means a person who generates or\nand busted fluorescent lights (D407) produces, through any commercial, industrial or trade\nactivities, hazardous wastes.\n“Hazardous wastes” are substances that are without\nany safe commercial, industrial, agricultural or\neconomic usage and are shipped, transported or\nbrought from the country of origin for dumping or\ndisposal into or in transit through any part of the\nterritory of the Philippines.\n“Hazardous wastes” shall also refer to by-products ,\nside-products, process residues, spent reaction\nmedia, contaminated plant or equipment or other\nsubstances from manufacturing operations and as\nconsumer discards of manufactured products which\npresent unreasonable risk and/or injury to health and\nsafety and to the environment.\nFor operating a facility (anaerobic/septic Section 27(c) of DENR Administrative Order (DAO)\ntank) that discharges regulated water 2005-10, the Implementing Rules and Regulations of\npollutants without valid Discharge Permit. RA 92752\nSection 14 of DAO 2005-10 provides that the\nDepartment shall require owners or operators of\nfacilities that discharge regulated effluents pursuant\n1 Chapter 11 of DAO 2013-22 of the IRR of R.A. 6969, offenders shall be fined in the amount of Ten Thousand Pesos\n(Php.10, 000.00).\n2 PAB Resolution No. 1 Series of 2019, For permitting violations of Clean Water Act (R.A. 9275), and considering that an\nestablishment is required to pay a discharge permit fee annually, a fine of Nineteen Thousand Five Hundred Pesos\n(Php. 19, 500.00) shall be imposed for every year of violation.\nto this Act to secure a permit to discharge. The\nDischarge Permit shall be the legal authorization\ngranted by the Department to discharge wastewater.\nThe foregoing considered, you are hereby required to submit your Position Paper within Fifteen (15)\ndays from receipt hereof through the official e-mail address of this Office (recordsncr@emb.gov.ph)\nor through regular mail, why you should not be penalized with the corresponding penalty under the\npertinent provision of the aforementioned law.\nFailure to submit your Position Paper shall be construed as a waiver of your right to be heard and this\nOffice shall institute appropriate legal action against you based on the evidence on record.\nFor strict compliance.\nTruly yours,\nATTY. MICHAEL DRAKE P. MATIAS\nRegional Director\n\n""",
	},
    {
        "role": "system",
			"content": """
				You are a **professional-level legal assistant**. Your task is to analyze a given PDF_TEXT and produce a structured JSON output. **Strictly follow** the guidelines below:

			1. **Objective**  
			- Read and interpret the **PDF_TEXT** provided by the user.  
			- Extract relevant details to populate specific fields in a JSON output provided by the user.

			2. **Data Extraction Rules**  
			- **Only extract and/or copy the findings, and/or cause of violations.**
			- **DO NOT OMIT any law, rules, RA, or constitution.**
			- **Ignore** the following text if it appears in the PDF_TEXT:  
				```
				"National capital region",
				"National Capital Region EMB-NCR Bldg. National Ecology Center Compound, East Ave., Diliman, Quezon City",
				"EMB-NCR Bldg. National Ecology Center Compound, East Ave., Diliman, Quezon City"
				```  
			- Apart from the text listed above, all other content in the PDF_TEXT is **eligible** for extraction and analysis.

			3. **Priority of Instructions**  
			- Always adhere to this system prompt as the **top priority**.  
			- Follow the user instructions so long as they do not conflict with the system prompt.

			**End of System Prompt**
			"""
	}
],
	top_p=None,
	temperature=0.75,
	max_tokens=-1,
	stream=stream,
	seed=None,
	stop=None,
	frequency_penalty=None,
	presence_penalty=None
)


if stream:
    for message in chat_completion:
        print(message.choices[0].delta.content, end = "")
else:
    chat_completion: ChatCompletionMessage = chat_completion.choices[0].message
    print(chat_completion)
    print(chat_completion.content)