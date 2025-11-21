import openai

class AIModule:
    """
    Lightweight wrapper around the OpenAI Responses API with minimal chat history.

    Parameters
    ----------
    openai_api_key : str
        OpenAI API key.
    model : str
        Model name.
    reasoning_effort : str
        Reasoning effort parameter for the Responses API
    system_prompt : str
        System message that initializes the conversation.

    Attributes
    ----------
    _client : openai.OpenAI
        Low-level OpenAI client instance.
    _model : str
        Chosen model name.
    _reasoning_effort : str
        Reasoning effort setting passed to the API.
    _system_prompt : str
        Stored system prompt.
    _history : list of dict
        Message history in Responses API format. First message is the system prompt.
    """

    def __init__(
        self,
        openai_api_key: str,
        model: str,
        reasoning_effort: str,
        system_prompt: str
    ):
        self._client = openai.AzureOpenAI(
            api_key=openai_api_key,
            api_version='2025-03-01-preview',
            azure_endpoint='https://aicc-fit-openai.openai.azure.com/'
        )
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._system_prompt = system_prompt
        self._history = [{'role': 'system', 'content': self._system_prompt}]

    def query(self, user_prompt: str) -> str:
        """
        Append a user message to history, call the model, and return assistant text.

        Parameters
        ----------
        user_prompt : str
            The content of the user message to send.

        Returns
        -------
        str
            Assistant response text (`response.output_text`) from the API.
        """
        self._history.append({'role': 'user', 'content': user_prompt})
        response = self._client.responses.create(
            model=self._model,
            reasoning={'effort': self._reasoning_effort},
            input=self._history,
            store=False
        )
        self._history.append({'role': 'assistant', 'content': response.output_text})
        return response.output_text
