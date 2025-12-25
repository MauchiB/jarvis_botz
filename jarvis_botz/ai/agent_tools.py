from langchain.agents import create_agent
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import OpenWeatherMapQueryRun, WikipediaQueryRun

from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.document_loaders import WebBaseLoader, YoutubeLoader
import os
import dotenv

from datetime import datetime

from langchain_experimental.utilities import PythonREPL

from youtube_transcript_api import YouTubeTranscriptApi

dotenv.load_dotenv()

@tool
def get_current_time() -> str:
    """
    Returns the current date, time, and day of the week.
    Use this tool when the user asks about the current time, today's date, 
    or what day it is.
    """


    now = datetime.now()
    return now.strftime("%A, %d %B %Y, %H:%M:%S")


@tool
def fetch_webpage_content(url: str) -> str:
    """
    Useful for fetching and reading the text content of a specific URL/webpage.
    Use this tool when the user provides a link or asks to summarize a website.
    Input should be a complete URL (e.g., https://example.com).
    """
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        
        if not docs:
            return "Error: The webpage is empty or could not be reached."
            
        # Убираем лишние пробелы и пустые строки для экономии токенов
        content = " ".join(docs[0].page_content.split())
        
        return content[:4000] # 1000 может быть мало для смысла, 4000 — золотая середина
    except Exception as e:
        return f"Error while loading the page: {str(e)}"
    
import traceback
@tool
def summarize_youtube_video(url: str) -> str:
    """
    Use this tool to get the transcript of a YouTube video. 
    Useful when a user asks questions about a video or needs a summary.
    Input: a YouTube video URL.
    """
  
    try:
        loader = YoutubeLoader.from_youtube_url(url, language=['en', 'ru'])
        docs = loader.load()
        print(docs)
        return docs[0].page_content[:1500] # Возвращаем текст для анализа нейросетью
    except Exception as e:
        tb = traceback.format_exc()
        
        print(tb)
        return f"Error: Could not extract transcript. {str(e)}"


import requests

@tool
def get_crypto_price(coin_id: str, vs_currency: str = "usd") -> str:
    """
    Useful for getting the current price of a cryptocurrency.
    Input 'coin_id' should be the name of the coin (e.g., 'bitcoin', 'ethereum', 'solana').
    Input 'vs_currency' is the target currency (default is 'usd').
    """
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id.lower()}&vs_currencies={vs_currency.lower()}"
    try:
        response = requests.get(url)
        data = response.json()
        if coin_id.lower() in data:
            price = data[coin_id.lower()][vs_currency.lower()]
            return f"The current price of {coin_id} is {price} {vs_currency.upper()}."
        else:
            return f"Could not find price for {coin_id}."
    except Exception as e:
        return f"Error fetching crypto price: {str(e)}"
    

'''
@tool
def search_in_documents(query: str) -> str:
    """
    Use this tool to search for specific information in the company's internal documents
    about prices, rules, and services.
    """
    # Здесь логика обращения к вашей векторной базе (ChromaDB, FAISS или Pinecone)
    # docs = vector_db.similarity_search(query)
    return "Result from database..."


'''


repl = PythonREPL()


@tool
def python_calculator(code: str) -> str:
    """
    A Python shell. Use this to execute python commands. 
    Input should be a valid python command. 
    If you want to see the output, you MUST use print().
    """
    try:
        # Убедимся, что repl инициализирован
        output = repl.run(code)
        print(f'out {output}')
        
        # Если кода выполнился, но в консоль ничего не вывелось
        if not output:
            return "Execution completed successfully, but there was no output (print). Remember to use print() to see results."
            
        return f"Execution result:\n{output}"
    except Exception as e:
        # Возвращаем саму ошибку кода, чтобы ИИ мог её исправить
        return f"Code error: {str(e)}"

os.environ['TAVILY_API_KEY'] = os.getenv('TAVILY_API_KEY')
tavily = TavilySearchResults(max_results=2, search_depth='basic')

wiki_wrap = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500, lang='en')
wiki = WikipediaQueryRun(api_wrapper=wiki_wrap)


tools = [tavily, wiki, get_current_time, fetch_webpage_content, summarize_youtube_video, get_crypto_price, python_calculator]

    


            
