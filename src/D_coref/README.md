## Important Information
### Coreference resolution was tried with different approaches:

- using the Python module **crosslingual-coreference** by David Berenstein
- using the spacy plugin **coreferee** by spacy and now maintained by Richard Paul Hudson
- using Generative LLMs to let a LangChain agent extract coreferences

The two best approaches were:
- **crosslingual-coreference** by David Berenstein
- a Generative LLM (OpenAI 4o with LangChain)

### The two best approaches were implemented in isolated environments using docker containers. This was due to module version incompatibilities and unresolvable dependency conflicts.
The two best approaches were implemented with these publicly available docker images:
- **ghcr.io/rainergo/img-xx-coref**: **crosslingual-coreference** by David Berenstein
  - The docker image is publicly available and will be downloaded from my Github repository once the Dockerfile is run with docker commands.
  - The docker image can also be built by using the Dockerfile in this directory: **img_xx_coref_files**


- **ghcr.io/rainergo/img-llm-extract-coref**: a Generative LLM (OpenAI 4o with LangChain)
  - The docker image is publicly available and will be downloaded from my Github repository once the Dockerfile is run with docker commands.
  - The docker image can be built by using the Dockerfile in this directory: **img_llm_extract_coref_files**


### Thus: *This D_coref* folder is only used to show the difference between the two best performing approaches. It requires that the docker containers are started.
