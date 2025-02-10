import os
from docxtpl import DocxTemplate

class WordPlaceholderReplacer:
    def __init__(self):
        """
        Initializes the WordPlaceholderReplacer with input and output file paths.
        """
        self._template_file = None
        self._output_file = None
        self._template = None

    @property
    def save_file(self):
        return self._output_file

    @save_file.setter
    def save_file(self, path):
        self._output_file = path

    @property
    def template_file(self):
        return self._template_file

    @template_file.setter
    def template_file(self, path):
        self._template_file = path
        self._template = DocxTemplate(path)

    def replace_placeholders(self, replacements):
        """
        Replaces placeholders in the Word document using the provided replacements dictionary.

        Args:
            replacements (dict): A dictionary where keys are placeholder names.
        """
        processed_replacements = {
            key: self._clean_value(value)
            for key, value in replacements.items()
        }

        self._template.render(processed_replacements)

    def _clean_value(self, value):
        """
        Removes any newline characters from list items or strings and joins lists into a single string.
        
        Args:
            value (str or list): The replacement value to be cleaned.
        
        Returns:
            str: Cleaned and concatenated value.
        """
        if isinstance(value, list):
            return " ".join(item.replace("\n", " ").strip() for item in value)
        elif isinstance(value, str):
            return value.replace("\n", " ").strip()
        return value  

    def save(self, filename):
        """Saves the modified Word document to the output file."""
        path = os.path.join(self.save_file, f"{filename}.docx")
        self._template.save(path)

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