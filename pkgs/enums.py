from enum import Enum

class TemplateType(Enum):
    AIR = "air"
    HW = "hw"
    PD = "pd"
    WATER = "water"

class TemplateFile(Enum):
    HW_REPLY = "templates/order_hw_reply.docx"
    HW_NO_REPLY = "templates/order_hw_no_reply.docx"
    PD_REPLY = "templates/order_pd_reply.docx"
    PD_NO_REPLY = "templates/order_pd_no_reply.docx"
    AIR_REPLY = "templates/order_air_reply.docx"
    AIR_NO_REPLY = "templates/order_air_no_reply.docx"
    WATER_REPLY = "templates/order_water_reply.docx"
    WATER_NO_REPLY = "templates/order_water_no_reply.docx"

    @staticmethod
    def get_template_file(template_type: TemplateType, include_reply: bool) -> str:
        """
        Returns the file path based on the template type and whether a reply is included.
        """
        if template_type == TemplateType.HW:
            return TemplateFile.HW_REPLY.value if include_reply else TemplateFile.HW_NO_REPLY.value
        elif template_type == TemplateType.PD:
            return TemplateFile.PD_REPLY.value if include_reply else TemplateFile.PD_NO_REPLY.value
        if template_type == TemplateType.WATER:
            return TemplateFile.WATER_REPLY.value if include_reply else TemplateFile.WATER_NO_REPLY.value
        elif template_type == TemplateType.AIR:
            return TemplateFile.AIR_REPLY.value if include_reply else TemplateFile.AIR_NO_REPLY.value
        else:
            raise ValueError(f"No template available for {template_type.value} with reply={include_reply}")
