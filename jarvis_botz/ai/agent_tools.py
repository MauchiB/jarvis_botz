from langchain.tools import tool, BaseTool
from langchain_community.tools import WikipediaQueryRun

from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.document_loaders import WebBaseLoader, YoutubeLoader

from typing import List
import traceback
from datetime import datetime


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
        return docs[0].page_content[:1500] # Возвращаем текст для анализа нейросетью
    except Exception as e:
        tb = traceback.format_exc()
        
        print(tb)
        return f"Error: Could not extract transcript. {str(e)}"



wiki_wrap = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500, lang='en')
wiki = WikipediaQueryRun(api_wrapper=wiki_wrap)



tools: List[BaseTool] = [wiki, get_current_time, fetch_webpage_content, summarize_youtube_video]

    

