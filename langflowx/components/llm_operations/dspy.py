import json
from typing import Any

import dspy
from langchain_openai import ChatOpenAI
from lfx.custom.custom_component.component import Component
from lfx.inputs import HandleInput
from lfx.inputs.inputs import InputTypes
from lfx.io import CodeInput, Output
from lfx.schema.data import Data
from lfx.schema.dotdict import dotdict
from lfx.schema.message import Message
from pydantic import SecretStr
from pydantic.fields import FieldInfo

'''
## Example1:
> One input, one output field.

```py
class Sentiment(dspy.Signature):
    """Classify the sentiment of a given sentence."""

    sentence: str = dspy.InputField()
    sentiment: str = dspy.OutputField(desc="positive, negative, or neutral")
```

- input: I love this movie, it was fantastic!
- output: { "sentiment": "positive" }

## Example2:
> One input, multiple specific output fields.

```py
class AspectSentiment(dspy.Signature):
    """Extract specific aspect, its sentiment, and the supporting reason from a sentence."""

    sentence: str = dspy.InputField()
    aspect: str = dspy.OutputField(desc="the specific feature of the movie being discussed")
    sentiment: str = dspy.OutputField(desc="positive, negative, or neutral")
    reason: str = dspy.OutputField(desc="the specific phrase from the text supporting the sentiment")
```

- input: The special effects in the movie were breathtaking, but the plot was predictable and the ending felt rushed.
- output: { "aspect": "visual effects", "sentiment": "positive", "reason": "breathtaking" }

## Example3:
> Multiple inputs, multiple output fields.

```py
class ContextualAnalysis(dspy.Signature):
    """Analyze the review based on specific movie context to identify focus and emotional depth."""

    sentence: str = dspy.InputField(desc="The user review text")
    movie_context: str = dspy.InputField(desc="Additional background like director or genre")

    primary_focus: str = dspy.OutputField(desc="What the review is mainly about (e.g., acting, directing, atmosphere)")
    emotional_depth: str = dspy.OutputField(desc="How intense the emotion is: low, medium, or high")
    key_takeaway: str = dspy.OutputField(desc="A brief summary of the user's final verdict")
```

- input:
  - sentence: I've been waiting for this sequel for years, and it absolutely exceeded every single expectation I had! I'm still shaking from the excitement.
  - movie_context: Directed by Denis Villeneuve, Sci-Fi epic.
- output: { "primary_focus": "overall quality and expectations", "emotional_depth": "high", "key_takeaway": "An overwhelming success that surpassed years of anticipation." }
'''

DEFAULT_SIGNATURE_CODE = '''
import dspy


class Sentiment(dspy.Signature):
    """Classify the sentiment of a given sentence."""

    sentence: str = dspy.InputField()
    sentiment: str = dspy.OutputField(desc="positive, negative, or neutral")
'''.strip()


class DSPyComponent(Component):
    name = "DSPy"
    display_name = "DSPy"
    description = "Run a DSPy Signature (optionally restoring program state JSON)."
    icon = "sparkles"

    inputs = [
        CodeInput(
            name="signature_code",
            display_name="Signature Code",
            info="Python code that defines a dspy.Signature subclass.",
            real_time_refresh=True,
            value=DEFAULT_SIGNATURE_CODE,
        ),
        HandleInput(
            name="state",
            display_name="State",
            info="Compiled program state as JSON (Message or Data). Optional.",
            input_types=["Message", "Data"],
            required=False,
        ),
        HandleInput(
            name="llm",
            display_name="Language Model",
            info="The language model to use to generate the structured output.",
            input_types=["LanguageModel"],
            required=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Result",
            name="message_output",
            method="generate_message_output",
        ),
        Output(
            display_name="Result",
            name="data_output",
            method="generate_data_output",
        ),
    ]

    def update_build_config(
        self, build_config: dotdict, field_value: Any, field_name: str | None = None
    ) -> dotdict:
        new_build_config = super().update_build_config(
            build_config, field_value, field_name
        )

        if field_name == "signature_code":
            self._update_inputs(build_config, build_config)
        return new_build_config

    def _update_inputs(
        self, new_build_config: dict[str, Any], current_build_config: dict[str, Any]
    ):
        custom_keys: list[str] = []

        _, input_names, _ = self._prepare_signature_metadata()
        for item in input_names.items():
            new_input: dict[str, Any] = _make_lfx_input(**item)
            name = new_input["name"]
            if "display_name" not in new_input:
                new_input["display_name"] = f"Args: {name}"

            if (
                name in current_build_config
                and current_build_config[name]["type"] == new_input["type"]
            ):
                current_value = current_build_config[name]["value"]
                if current_value != "":
                    new_input["value"] = current_value

            new_build_config[name] = new_input
            custom_keys.append(name)

        del_keys = [
            k
            for k in new_build_config.keys()
            if k not in DSPyComponent.inputs and k not in custom_keys
        ]
        if del_keys:
            for key in del_keys:
                del new_build_config[key]

        return new_build_config

    def _get_model_param(self) -> dict[str, Any]:
        model = self.llm
        # LocalOpenAI/OpenAI
        if isinstance(model, ChatOpenAI):
            raw: dict[str, Any] = model.model_dump(exclude_none=True)
            model_name: str = raw.pop("model_name", None)
            if not model_name.startswith("openai/"):
                model_name = f"openai/{model_name}"
            return {
                "model": model_name,
                "api_base": raw.pop("openai_api_base", None),
                "api_key": raw.pop("openai_api_key", None),
                **raw,
            }
        return {}

    def _prepare_signature_metadata(
        self,
    ) -> tuple[type[dspy.Signature], dict[str, FieldInfo], dict[str, FieldInfo]]:
        signature_cls = _extract_signature_from_code(self.signature_code)

        input_fields: dict[str, FieldInfo] = getattr(
            signature_cls, "input_fields", None
        )
        if not input_fields:
            msg = "Signature must define at least one InputField."
            raise ValueError(msg)

        output_fields: dict[str, FieldInfo] = getattr(
            signature_cls, "output_fields", None
        )
        if not output_fields:
            msg = "Signature must define at least one OutputField."
            raise ValueError(msg)

        return signature_cls, input_fields, output_fields

    async def _run_predict(self) -> tuple[dict[str, Any], str]:
        (
            signature_cls,
            input_names,
            output_names,
        ) = self._prepare_signature_metadata()

        model_params = self._get_model_param()
        model_name = model_params.get("model")
        if not model_name:
            msg = "A model selection is required"
            raise ValueError(msg)
        api_base = model_params.get("api_base")
        api_key = model_params.get("api_key")
        if isinstance(api_key, SecretStr):
            api_key = api_key.get_secret_value()

        lm = dspy.LM(model_name, api_base=api_base, api_key=api_key)

        with dspy.context(lm=lm):
            program = dspy.Predict(signature_cls)

            state = _state_to_dict(getattr(self, "state", None))
            if state and hasattr(program, "load_state"):
                # Restore compiled/teleprompted parameters if available.
                program.load_state(state)  # type: ignore[attr-defined]

            input_kwargs = {k: getattr(self, k) for k in input_names.keys()}
            pred = program(**input_kwargs)

        pred_dict: dict[str, Any] = pred.toDict()
        return {k: pred_dict.get(k) for k in output_names.keys()}

    async def generate_message_output(self) -> Message:
        payload = await self._run_predict()
        return Message(
            text="```json\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n```"
        )

    async def generate_data_output(self) -> Data:
        pred_dict = await self._run_predict()
        return Data(data=pred_dict)


def _json_loads_maybe(s: str) -> Any:
    s0 = (s or "").strip()
    if not s0:
        return None
    return json.loads(s0)


def _extract_signature_from_code(signature_code: str) -> type[dspy.Signature]:
    namespace: dict[str, Any] = {}
    # Execute user-provided Signature definition (DSPy expects real Python objects).
    exec(compile(signature_code, "<dspy_signature>", "exec"), namespace)

    # Pick the last public Signature subclass defined in the snippet.
    candidates: list[type[dspy.Signature]] = []
    for name, obj in namespace.items():
        if name.startswith("_"):
            continue
        if isinstance(obj, type) and issubclass(obj, dspy.Signature):
            if obj is not dspy.Signature:
                candidates.append(obj)
    if not candidates:
        msg = "No dspy.Signature subclass found in Signature code."
        raise ValueError(msg)
    return candidates[-1]


def _state_to_dict(state_input: Any) -> dict[str, Any] | None:
    if state_input is None or state_input == "":
        return None

    if isinstance(state_input, Message):
        raw = state_input.text
        if isinstance(raw, str) and raw.strip():
            loaded = _json_loads_maybe(raw)
            return loaded if isinstance(loaded, dict) else {"value": loaded}
        return None

    if isinstance(state_input, Data):
        return state_input.data

    if isinstance(state_input, dict):
        return state_input

    if isinstance(state_input, str):
        loaded = _json_loads_maybe(state_input)
        return loaded if isinstance(loaded, dict) else {"value": loaded}

    return {"value": state_input}


def _make_lfx_input(name: str, fi: FieldInfo) -> InputTypes:
    _ = {
        "sentiment": FieldInfo(
            annotation=str,
            required=True,
            json_schema_extra={
                "desc": "positive, negative, or neutral",
                "__dspy_field_type": "output",
                "prefix": "Sentiment:",
            },
        )
    }

    return ...  # pyright: ignore[reportReturnType]
