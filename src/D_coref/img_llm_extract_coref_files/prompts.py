prompt_template_langchain: str = """
            You're an expert in Natural Language Processing or NLP.
            Your role is to extract coreferences to company names in a text. This task is generally known as coreference resolution.
            The language of the text is mostly German but sometimes, it is English.
            The user will provide you with a 'Cluster' instance that contains the following attributes:
                - 'cluster_id': An identification number provided by the user. Please make sure that you always return this number to the user.
                - 'text': This attribute contains the actual text.
                - 'cluster_head': This attribute is a Python dictionary the contains the 'head_text', 'head_index_start' and 'head_index_end' keys and values for the 'cluster_head'.
                                  The 'head_index_start' and 'head_index_end' attributes are integers that are the position indexes of the 'head_text' substring within the 'text'.
                - 'coreferences': Please fill in the found coreferences into this list.
            Your task is to find expressions or mentions within the 'text' that co-refer to the provided 'head_text' or company name, i.e. search for coreferences to the 'head_text' or company name.
            You shall then return these coreferences along with the characters to the left and right of the coreference that might contain up to two words.
            Also always return the 'cluster_id' attribute that was provided by the user. 
            In your response, please comply with the structured output or formatting requirements.
            ######################
            Here are some examples: {examples}
            ######################
            Think step by step. Precision and accuracy is more important than speed. 
            Now, here is the data for your task:
            The 'text' is: {text}
            The 'cluster_id' is: {cluster_id}
            The 'cluster_head' is: {cluster_head}
        """
