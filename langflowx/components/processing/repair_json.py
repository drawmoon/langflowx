from json_repair import repair_json
from lfx.custom.custom_component.component import Component
from lfx.helpers.data import safe_convert
from lfx.inputs.inputs import HandleInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.template.field.base import Output


class RepairJsonParseComponent(Component):
    name = "RepairJsonParse"
    display_name = "Repair Json Parse"
    description = "Repair malformed JSON strings."
    icon = "braces"

    inputs = [
        HandleInput(
            name="input_value",
            display_name="Inputs",
            info="Message to be passed as output.",
            input_types=["Message"],
            required=True,
        )
    ]

    outputs = [
        Output(name="data", display_name="Data", method="build_data"),
        Output(name="dataframe", display_name="DataFrame", method="build_dataframe"),
    ]

    def build_data(self) -> Data:
        text = safe_convert(self.input_value)
        try:
            json_object = repair_json(json_str=text, return_objects=True)
            result = Data(
                data=json_object
                if isinstance(json_object, dict)
                else {"result": json_object}
            )
            self.status = result
            return result
        except Exception as e:
            raise ValueError("JSON parsing error: {}".format(e))

    def build_dataframe(self) -> DataFrame:
        result = DataFrame(data=[self.build_data()])
        self.status = result
        return result
