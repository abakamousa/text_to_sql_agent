from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.models.settings import settings
import logging


class OpenAIClient:
    """Wrapper around Azure OpenAI (via LangChain)."""

    def __init__(self, deployment_name: str | None = None):
        self.deployment_name =deployment_name or settings.azure_openai_deployment
        self.api_version = settings.azure_openai_api_version
        self.endpoint =settings.azure_openai_endpoint
        self.api_key = settings.azure_openai_api_key
        #self.temperature = temperature

        logging.info(f"🔧 Azure OpenAI Config:")
        logging.info(f"  Endpoint: {self.endpoint}")
        logging.info(f"  Deployment: {self.deployment_name}")
        logging.info(f"  Version: {self.api_version}")
        
        #logging.info(f" Azure OpenAI endpoint: {settings.azure_openai_endpoint}")
        if not self.endpoint or not self.deployment_name:
            raise ValueError("Missing Azure OpenAI configuration.")

        self.llm = AzureChatOpenAI(
            deployment_name=self.deployment_name,
            openai_api_version=self.api_version,
            azure_endpoint=self.endpoint,
            #temperature=self.temperature,
        )

    def get_llm(self):
        """Return the raw LangChain LLM instance."""
        return self.llm

    def run_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Run a simple system + user prompt and return plain text output."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", f"{user_prompt}"),
            ]
        )

        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"user_prompt": user_prompt})
