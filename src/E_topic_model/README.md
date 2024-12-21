## Important Information
### Topic Modelling was tried with different approaches:

- using traditional methods such as One-Hot-Encoders, TF-IDF, Bag-Of-Words, Clustering
- using Embedding-like approaches such as SentenceTransformers and a proprietary implementation of BERTopic
- using Generative LLMs to let a LangChain agent extract topics

The two best approaches were:
- a proprietary implementation of BERTopic
- a Generative LLM (OpenAI 4o with LangChain)

### One of the two best approaches were implemented in an isolated environment using a docker container. This was due to module version incompatibilities and unresolvable dependency conflicts.
- **ghcr.io/rainergo/img-llm-extract-topic**: Generative LLM (OpenAI 4o model) with LangChain
  - The docker image is publicly available and will be downloaded from my Github repository once the Dockerfile in the **gen_llm_files** folder is run with docker commands.
  - The docker image can also be built by using the Dockerfile in this directory: **img_llm_extract_topic**

### For the second-best approach "TF-IDF" and "Clustering", the files are located in the "traditional" folder.
