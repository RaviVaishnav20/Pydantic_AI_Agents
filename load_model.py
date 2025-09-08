from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.gemini import GeminiModel
from dotenv import load_dotenv
load_dotenv()
# GROQ_MODEL = 'llama-3.1-8b-instant'
# OPENAI_MODEL = 'openai:gpt-5 nano'
## OLLAMA_MODEL = 'ollama:llama3:8b'
# GEMINI_MODEL = 'gemini-2.5-flash'


# GROQ_MODEL = GroqModel('llama-3.1-8b-instant')
OPENAI_MODEL = OpenAIChatModel("gpt-5-nano")
# OLLAMA_MODEL(
# GEMINI_MODEL = GeminiModel('gemini-2.5-flash')


