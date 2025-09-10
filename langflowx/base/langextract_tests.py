# import os

# from langutil_llm.langextract import Example, ExampleData, LangExtractor

# MODEL_BASE_URL = os.getenv("MODEL_BASE_URL", "http://localhost:8750/v1")
# MODEL_EXTRACTOR = os.getenv("MODEL_EXTRACTOR")


# def test_extractor():
#     examples = [
#         ExampleData(
#             text="ROMEO. But soft! What light through yonder window breaks? It is the east, and Juliet is the sun.",
#             extractions=[
#                 Example(
#                     extraction_class="character",
#                     extraction_text="ROMEO",
#                     attributes={"emotional_state": "wonder"},
#                 ),
#                 Example(
#                     extraction_class="emotion",
#                     extraction_text="But soft!",
#                     attributes={"feeling": "gentle awe"},
#                 ),
#                 Example(
#                     extraction_class="relationship",
#                     extraction_text="Juliet is the sun",
#                     attributes={"type": "metaphor"},
#                 ),
#             ],
#         ),
#     ]
#     extractor = LangExtractor(
#         model=MODEL_EXTRACTOR,
#         base_url=MODEL_BASE_URL,
#         api_key="abc",
#         examples=examples,
#     )
#     annotated_documents = extractor.invoke(
#         "Lady Juliet gazed longingly at the stars, her heart aching for Romeo"
#     )
#     assert len(annotated_documents.extractions) > 0
