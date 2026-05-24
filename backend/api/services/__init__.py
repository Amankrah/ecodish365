"""Service-layer classes for the api app (CNF matcher, recipe decomposer, etc.).

Each module here exposes a single concern (CNFMatcher, CNFRecipeDecomposer, …)
and is consumed by the api views without those views having to know about
embedding models, prompt templates, or OpenAI clients directly.
"""
