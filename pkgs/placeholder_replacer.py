import os
import traceback

import xml.sax.saxutils as saxutils
from docxtpl import DocxTemplate
from pkgs.dataclass import Document
from pkgs.misc import Utils


class WordPlaceholderReplacer:

    def __init__(self):
        """
        Initializes the WordPlaceholderReplacer with input and output file paths.
        """
        self._template_file = None
        self._save_location = None
        self._template = None

    @property
    def save_location(self):
        return self._save_location

    @save_location.setter
    def save_location(self, path):
        self._save_location = path

    @property
    def template_filepath(self):
        return self._template_file

    @template_filepath.setter
    def template_filepath(self, path):
        self._template_file = path
        self._template = DocxTemplate(path)

    def draft_dismissal(self, document: Document) -> Document:
        try:
            # document.doc_payload.validate()
            api_data = document.doc_payload
        except Exception as e:
            document.doc_payload.error_occured = e
            return document
        try:
            # path = Path(document.save_filepath)
            # if path.is_file():
            #     # print(f"{path} is a file")
            #     return

            case_number: str = api_data.api_response.get("case_number")
            api_data.api_response["case_number_only"] = case_number[-9:]

            self._replace_placeholders(api_data.api_response)
            doc_filepath = self._save(document.temp_doc_data.save_path, case_number, document.temp_doc_data.selected_template)
            
            document.file_name = os.path.basename(doc_filepath)
            document.save_filepath = doc_filepath
            
            return document
        except Exception as e:
            print(traceback.format_exc())
            document.doc_payload.status = "Error"
            document.doc_payload.error_occured = e
            return document

    def _replace_placeholders(self, replacements: dict):
        """
        Replaces placeholders in the Word document using the provided replacements dictionary.

        Args:
            replacements (dict): A dictionary where keys are placeholder names.
        """
        def escape_xml(value):
            """Escape XML special characters in strings and ensure each string ends with a period."""  
            if isinstance(value, str):  
                escaped = saxutils.escape(value)  
                
                if not escaped.endswith('.'):  
                    escaped += '.'  
                return escaped  
            elif isinstance(value, list):  
                
                return [escape_xml(item) for item in value]  
            return value  

        clean = {
            key: escape_xml(value) for key, value in replacements.items()
        }

        self._template.render(clean)
        return replacements

    def _clean_value(self, value):
        """
        Removes any newline characters from list items or strings and joins lists into a single string.
        
        Args:
            value (str or list): The replacement value to be cleaned.
        
        Returns:
            str: Cleaned and concatenated value.
        """
        def add_period(text: str):
            text = text.strip()  
            
            if text and not text.endswith('.'):
                return text + '.'
            return text
        
        if isinstance(value, list):
            cleaned_items = []
            for item in value:
                
                if not isinstance(item, str):
                    item = str(item)
                
                cleaned_item = add_period(item.replace("\n", ""))
                cleaned_items.append(cleaned_item)
            
            return " ".join(cleaned_items)
        elif isinstance(value, str):
            return value.replace("\n", "").strip()
        return value 

    def _save(self, save_location, filename, template_type) -> str:
        """Saves the modified Word document to the output file."""
        try:
            new_path = Utils.get_unique_filename(save_location, filename, template_type)
            self._template.save(new_path)
            return new_path
        except Exception:
            print(traceback.format_exc())

if __name__ == "__main__":
    data = {
    "client_name": "KASSEL RESIDENCES PARAÑAQUE",
    "location": "E. Rodriguez Avenue, La Huerta, Parañaque City",
    "case_number": "NOV-EMB-NCR-2022-1664",
    "date_of_inspection": "31 March 2022",
    "violations": [
        "For having/operating air pollution source Section 1, Rule XIX of the Implementing installments (Diesel Fuel Fire Pump) without Rules and Regulations (IRR) of the corresponding valid 'Permit to Operate' (PO). 'Philippine Clean Air Act of 1999' (RA 8749), as amended by DAO 2004-261",
        "For failure to put a billboard with a message Condition Number 3 of its ECC, pursuant to indicated in the said ECC Condition. the Revised Procedural Manual of DAO No. 30 series of 2003, the Implementing Rules and Regulations of PD 1586.2",
        "Condition Number 4 of its ECC, pursuant to For failure to conform with the provisions of RA 9275, RA 8749, and RA 6969 and its Revised Procedural Manual of DAO No. 30 series of 2003, the Implementing Rules and Regulations of PD 1586.3",
        "For failure to appoint/designate an accredited Condition Number 5 of its ECC, pursuant to Pollution Control Officer that monitors the Revised Procedural Manual of DAO No. 30 series of 2003, the Implementing Rules and Regulations of PD 1586.4",
        "Condition Number 5.2 of its ECC, pursuant to For failure to submit Compliance Monitoring Reports semi-annually every year since the year of 2009.",
        "For operating a facility (wastewater treatment plant) that discharges regulated water pollutants without Discharge Permit. Section 14 of DAO 2005-10 provides that the Department shall require owners or operators of facilities that discharge regulated effluents pursuant to this Act to secure a permit to discharge.",
        "For failure to register as hazardous waste generator considering the Respondent is ordered under Chapter 3.3 of the DENR Administrative Order (DAO) 2013-22, Revised Procedure and Standards for the Management of Hazardous Wastes."
    ],
    "case_number_only": "2022-1664"
    }
    replacer = WordPlaceholderReplacer()
    replacer.template_file = "C:\\Users\\omarg\\OrDraft\\templates\\order_hw_reply.docx"
    replacer.save_file = "."
    replacer.replace_placeholders(data)
    replacer.save("test")