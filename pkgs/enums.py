from enum import Enum

class Models(Enum):
    deepseek_r1_distill_llama_8b = "deepseek-r1-distill-llama-8b"
    # deepseek_r1_distill_qwen_1_5b = "lmstudio-community/deepseek-r1-distill-qwen-1.5b"

class TemplateType(Enum):
    DISMISSAL_AIR = "Dismissal - AIR"
    DISMISSAL_HW = "Dismissal - HW"
    DISMISSAL_PD = "Dismissal - PD"
    DISMISSAL_WATER = "Dismissal - Water"
    RESO_AIR = "Resolution - AIR" 
    RESO_HW = "Resolution - HW"
    RESO_PD = "Resolution - PD"
    RESO_WATER = "Resolution - Water"

class TemplateFile(Enum):
    DISMISSAL_HW_REPLY = "templates/order_hw_reply.docx"
    DISMISSAL_HW_NO_REPLY = "templates/order_hw_no_reply.docx"
    DISMISSAL_PD_REPLY = "templates/order_pd_reply.docx"
    DISMISSAL_PD_NO_REPLY = "templates/order_pd_no_reply.docx"
    DISMISSAL_AIR_REPLY = "templates/order_air_reply.docx"
    DISMISSAL_AIR_NO_REPLY = "templates/order_air_no_reply.docx"
    DISMISSAL_WATER_REPLY = "templates/order_water_reply.docx"
    DISMISSAL_WATER_NO_REPLY = "templates/order_water_no_reply.docx"

    RESO_HW = "templates/reso_hw.docx"
    RESO_PD = "templates/reso_pd.docx"
    RESO_AIR = "templates/reso_air.docx"
    RESO_WATER = "templates/reso_water.docx"
    # RESO_HW_NO_REPLY = "templates/reso_hw_no_reply.docx"
    # RESO_PD_NO_REPLY = "templates/reso_pd_no_reply.docx"
    # RESO_AIR_NO_REPLY = "templates/reso_air_no_reply.docx"
    # RESO_WATER_NO_REPLY = "templates/reso_water_no_reply.docx"

    @staticmethod
    def get_template_file(template_type: TemplateType, include_reply: bool) -> str:
        """
        Returns the file path based on the template type and whether a reply is included.
        """
        if template_type == TemplateType.DISMISSAL_HW:
            return TemplateFile.DISMISSAL_HW_REPLY.value if include_reply else TemplateFile.DISMISSAL_HW_NO_REPLY.value
        elif template_type == TemplateType.DISMISSAL_PD:
            return TemplateFile.DISMISSAL_PD_REPLY.value if include_reply else TemplateFile.DISMISSAL_PD_NO_REPLY.value
        if template_type == TemplateType.DISMISSAL_WATER:
            return TemplateFile.DISMISSAL_WATER_REPLY.value if include_reply else TemplateFile.DISMISSAL_WATER_NO_REPLY.value
        elif template_type == TemplateType.DISMISSAL_AIR:
            return TemplateFile.DISMISSAL_AIR_REPLY.value if include_reply else TemplateFile.DISMISSAL_AIR_NO_REPLY.value

        elif template_type == TemplateType.RESO_HW:
            return TemplateFile.RESO_HW.value
        elif template_type == TemplateType.RESO_PD:
            return TemplateFile.RESO_PD.value
        if template_type == TemplateType.RESO_WATER:
            return TemplateFile.RESO_WATER.value
        elif template_type == TemplateType.RESO_AIR:
            return TemplateFile.RESO_AIR.value
        else:
            raise ValueError(f"No template available for {template_type.value}")
