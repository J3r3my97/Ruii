"""Joe — an autonomous, AI-disclosed persona agent.

The runtime lives here and treats the legacy ``llm_engineering`` package as a
library (Mongo/Qdrant infrastructure, preprocessing, RAG utilities). Nothing in
``joe`` imports ZenML, Selenium, or the SageMaker/training code paths, so the
agent process stays slim and fast to import.
"""
