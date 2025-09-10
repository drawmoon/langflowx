# Langflowx

Langflowx is a customized version of Langflow that adds specific AI components and workflow utilities.

## ✨ Key Features

### Custom Components

- DSPy Integration: Native support for [DSPy signatures and programs](./docs/dspy/README.md).
- Extraction & Parsing: Includes LangExtract and RepairJsonParse for resilient data handling.
- Data Transformation: Built-in JQ support for JSON filtering and LLMRerank for search optimization.
- NLP Suite: Integrated NLP processing via HanLP and LTP.

## ⚡️ Quickstart

### Run with Just

Start the Langflowx service immediately:

```sh
just serve
```

### Development Setup

To debug the application in VS Code, use the following `launch.json` configuration:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Langflowx",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "args": [
                "run",
                "--components-path", "${workspaceFolder}/components",
                "--env-file", "${workspaceFolder}/.env"
            ],
            "envFile": "${workspaceFolder}/.env",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

### Environment Configuration (`.env`)

Configure your local environment variables for development and deployment:

```ini
# Server Settings
LANGFLOW_HOST=0.0.0.0
LANGFLOW_PORT=17860
LANGFLOW_DEV=true

# Authentication
LANGFLOW_SUPERUSER=admin
LANGFLOW_SUPERUSER_PASSWORD=admin
LANGFLOW_AUTO_LOGIN=true

# Infrastructure
LANGFLOW_WORKERS=1
LANGFLOW_CONFIG_DIR=.langflow
LANGFLOW_FRONTEND_PATH=www
LANGFLOW_SAVE_DB_IN_CONFIG_DIR=true
LANGFLOW_LANGCHAIN_CACHE=SQLiteCache
DO_NOT_TRACK=true
```

## 🚀 API Usage

You can interact with your flows programmatically using the following pattern:

```python
import uuid
import requests
from typing import Any
from json_repair import repair_json
from pyiter import it

def _parse_output(data: dict[str, Any]) -> dict[str, Any]:
    output = data["outputs"][0]["outputs"][0]
    component_id = output["component_id"]

    if "messages" in output:
        # Locate the specific message from the component
        message_data = it(output["messages"]).first(
            lambda x: x["component_id"] == component_id
        )
        message = message_data["message"]

        # Robust JSON parsing
        parsed = repair_json(message, return_objects=True, skip_json_loads=False)
        if isinstance(parsed, dict):
            return parsed
    
    raise ValueError("No valid output found in response.")

def request_flow(input_text: str):
    url = "http://localhost:17860/api/v1/run/<YOUR_FLOW_ID>"
    headers = {"x-api-key": "YOUR_API_KEY"}
    
    payload = {
        "input_value": input_text,
        "input_type": "chat",
        "output_type": "chat",
        "session_id": str(uuid.uuid4())
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    return _parse_output(response.json())
```