import json

import jq
from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput, MessageTextInput
from lfx.io import Output
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
from lfx.schema.message import Message


class JQComponent(Component):
    name = "JQ"
    display_name = "JQ"
    description = "Query and transform JSON data using JQ expressions."
    icon = "braces"

    inputs = [
        HandleInput(
            name="data",
            display_name="Data",
            info="Data or Message object to query with JQ expression. Data is assumed to be a dict, Message will be parsed from JSON.",
            input_types=["Data", "Message"],
            required=True,
            is_list=False,
        ),
        MessageTextInput(
            name="query",
            display_name="JQ Expression",
            info="JQ query expression to filter or transform the data. Example: .properties.id",
            placeholder="e.g., .properties.id",
            required=True,
        ),
    ]

    outputs = [
        Output(name="data_output", display_name="Data", method="build_data"),
        Output(
            name="dataframe_output", display_name="DataFrame", method="build_dataframe"
        ),
    ]

    def build_data(self) -> Data:
        result = self.json_query()
        data = (
            Data(data=result)
            if isinstance(result, dict)
            else Data(data={"result": result})
        )
        self.status = data
        return data

    def build_dataframe(self) -> DataFrame:
        result = self.json_query()
        data = (
            DataFrame(data=[result])
            if isinstance(result, dict)
            else DataFrame(data=result)
        )
        self.status = data
        return data

    def parse_input(self) -> dict[str, object] | list[dict[str, object]]:
        """Extract data dictionary from Data or Message object."""
        data = self.data

        def repair_json(s: str):
            try:
                import orjson
                from json_repair import repair_json

                # The json_loads function can be slow
                s = repair_json(s, return_objects=False, skip_json_loads=True)

                # Because json_loads verification is skipped, we strictly validate the JSON by parsing it again with orjson.
                parsed = orjson.loads(s)
            except (json.JSONDecodeError, TypeError) as e:
                raise ValueError("Failed to repair or parse the JSON string.") from e
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list) and isinstance(parsed[0], dict):
                return parsed
            raise ValueError(
                "Unable to parse Message text as JSON. Please make sure it contains valid JSON."
            ) from None

        if isinstance(data, Data):
            data = data.data
            if "text" in data and "flow_id" in data:
                return repair_json(str(data["text"]))
            return data

        if isinstance(data, Message):
            return repair_json(str(data.text))

        raise ValueError("Unsupported data type for get_data_dict.")

    def json_query(self) -> dict[str, object] | list[dict[str, object]]:
        """Execute JQ query on the input data."""
        if not self.query or not self.query.strip():
            msg = "JSON Query is required and cannot be blank."
            raise ValueError(msg) from None
        jq_input = self.parse_input()
        try:
            results = jq.compile(self.query).input(jq_input).all()
            if not results:
                msg = "No result from JSON query."
                raise ValueError(msg) from None
            result = results[0] if len(results) == 1 else results
            if result is None or result == "None":
                msg = "JSON query returned null/None. Check if the path exists in your data."
                raise ValueError(msg) from None
            return result
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"JSON Query failed: {e}")
            msg = f"JSON Query error: {e}"
            raise ValueError(msg) from e
