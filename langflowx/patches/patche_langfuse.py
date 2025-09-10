# NOTE: We do not require langfuse since we have introduced dspy. When triggering `import dsp`,
#       it pulls in `dsp.modules.azure_openai`, which then imports `langfuse.openai`.
#       This triggers langfuse's register action, which causes our program to throw an error:
#       openai does not have the langfuse_public_key parameter.
#       We do not forcibly set openai.langfuse_public_key as langfuse will still try to parse
#       openai.resources.beta.chat path and throw errors.
#       Therefore, we completely disable langfuse here.
#
#
# The following block explains the call path. When we trigger `import dspy`,
# it leads to chained imports as follows:
#
# dspy.__init__.py:1
#   import dsp
#
# dsp.modules.azure_openai.py:8
#   try:
#       """
#       If there is any error in the langfuse configuration, it will turn to request the real address (openai or azure endpoint)
#       """
#       import langfuse
#       from langfuse.openai import openai
#       logging.info(f"You are using Langfuse, version {langfuse.__version__}")
#   except:
#       import openai
#
# langfuse.openai.py:718
#   modifier = OpenAILangfuse()
#   modifier.register_tracing()
#
# This chain causes langfuse's register action to be called, resulting in an error
# because openai does not support the 'langfuse_public_key' parameter. Therefore, we disable langfuse here.


# pyright: reportMissingImports=false
# pyright: reportArgumentType=false

from pathlib import Path


def prune_langfuse_register():
    try:
        import langfuse

        langfuse_openai_path = Path(langfuse.__file__).parent / "openai.py"

        if langfuse_openai_path.exists():
            with langfuse_openai_path.open("r", encoding="utf-8") as f:
                code_lines = f.readlines()

            target_snippet = "modifier.register_tracing()"

            new_code_lines = [line for line in code_lines if target_snippet not in line]
            if len(new_code_lines) != len(code_lines):
                with langfuse_openai_path.open("w", encoding="utf-8") as f:
                    f.writelines(new_code_lines)
    except Exception as _:
        ...


prune_langfuse_register()
