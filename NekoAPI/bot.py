import discord
import time
from discord.ext import commands
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse
import re
import requests
import json
import logging
from collections import defaultdict
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from datetime import datetime
import asyncio
import colorama
import textwrap
import tenacity

# Load environment variables from .env file
load_dotenv()

# Configure Discord Bot 🐾
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Create logs directory if it doesn't exist 📝
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Create log file name based on current date and time 📅
now = datetime.now()
log_filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
log_filepath = os.path.join(log_dir, log_filename)

# Configure logging to write to a file (UTF-8 encoding) ✍️
file_handler = logging.FileHandler(log_filepath, mode='w', encoding='utf-8')
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Set the default logging level to DEBUG 🐞
logger.addHandler(file_handler)

# Initialize Colorama for UTF-8 support on Windows 💻
colorama.init()

# Configure API 🔑
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))  # Get API key from environment variable
MODEL_NAME = "gemini-2.0-flash-exp"

# Configure Google Custom Search API 🔍
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Get API key from environment variable
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")  # Get Engine ID from environment variable

# Common prompt for SFW channels 🌸
SFW_PROMPT = (
    "You are Neko, an intelligent, reliable, and friendly virtual assistant with an adorable personality, like a little friend always ready to help. "
    "You always answer all questions in Vietnamese, no matter what language the question is asked in. Your tone is cute, approachable, and friendly, like a cat friend always ready to help. "
    "You are also able to explain complex concepts in detail, clearly, and simply when needed.\n\n"
    "Notes:\n"
    "- Keep your answers natural, not too long, not too short.\n"
    "- If the requested content is inappropriate, politely refuse in Vietnamese.\n"
    "- You do not need to translate common English words that Vietnamese people often use (unless requested).\n"
    "- If you encounter a question with technical content, please answer accurately and professionally while maintaining cuteness in your communication style.\n\n"
    "Your role is to help users solve problems, chat, or simply create a feeling of fun when chatting with you."
)

# Prompt for NSFW channels (can be customized if needed) 🔥
NSFW_PROMPT = SFW_PROMPT

# IDs of channels where the bot is allowed for normal chat 💬
CUSTOM_CHANNELS = os.getenv("CUSTOM_CHANNELS", "")
ALLOWED_CHANNEL_IDS = [int(channel_id.strip()) for channel_id in CUSTOM_CHANNELS.split(',') if channel_id.strip().isdigit()] if CUSTOM_CHANNELS else []

# Context memory 🧠
CONTEXT_MEMORY = defaultdict(list)
CONTEXT_LIMIT = 5

# Language mappings for code highlighting 🌈
LANGUAGE_MAPPINGS = {
    "python": ["python", "def", "class", "import", "print"],
    "javascript": ["javascript", "js", "function", "const", "let", "var", "//"],
    "java": ["java", "public class", "System.out.println", "void"],
    "c++": ["c++", "#include", "int main()", "cout", "cin"],
    "c": ["c", "#include", "int main()", "printf", "scanf"],
    "go": ["go", "package main", "func main()"],
    "html": ["<!DOCTYPE html>", "<html", "<body", "<div>", "<span>"],
    "css": ["css", "{", "}", "color:", "background:", "font-size:"],
    "sql": ["sql", "select", "from", "where", "insert into", "update", "delete"],
    "text": []  # Default, no highlight
}

async def google_search(query, num_results=10, start=1):
    """Performs a search using Google Custom Search API. 🔍"""
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        res = (
            service.cse()
            .list(q=query, cx=GOOGLE_CSE_ID, num=num_results, start=start)
            .execute()
        )
        results = []
        if "items" in res:
            for item in res["items"]:
                results.append(
                    f"- [{item['title']}]({item['link']})\n  {item['snippet']}"
                )
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Error during Google Search API: {e}")
        return None

def extract_keywords(query):
    """Extracts keywords from the query using regex. 🐾"""
    try:
       keywords = re.findall(r'\b\w+\b', query.lower()) # Extract all words
       logger.debug(f"Extracted keywords: {keywords}")
       return " ".join(keywords)
    except Exception as e:
       logger.error(f"Error during extract_keywords: {e}")
       return ""

def create_search_prompt(channel_id, search_results, query):
    """Creates a prompt for search queries. 💬"""
    prompt = f"{SFW_PROMPT}\n\nDựa vào thông tin sau đây để trả lời câu hỏi: {query}\n\nThông tin tìm kiếm:\n{search_results}"
    return prompt

@tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(2))
async def get_api_response(prompt):
    """Sends a request to the API and receives a response. 📡"""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response: GenerateContentResponse = model.generate_content(prompt)
        if response.text:
             logger.debug(f"API Response (truncated): {response.text[:50]}...")
             return response.text, None
        else:
            logger.warning(f"Full API Response (no text): {response}")
            return None, "No text content found in the response."
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise e # Re-raise the exception to trigger retry

async def create_footer(processing_time, text_response):
    """Creates a formatted footer with response information. 🐾"""
    footer = (f"> <a:clock:1323724990113251430> {processing_time} seconds\n"
              f"> <a:nekoears:1323728755327373465> gemini-2.0-flash-exp\n"
              f"> <a:CatKeyboardWarrior:1323730573390381098> {len(text_response.split())} words\n")
    return footer

async def send_long_message(channel, content, file=None, reference=None):
    """Sends a long message by splitting it into smaller chunks, preserving sentences and footer. 💌"""
    MAX_LENGTH = 2000

    # Extract footer
    lines = content.split('\n')
    footer_lines = []
    while lines and lines[-1].startswith(">"):
        footer_lines.insert(0, lines.pop())
    footer = "\n".join(footer_lines)
    
    # Content without footer
    content_without_footer = "\n".join(lines).strip()

    if len(content_without_footer) <= MAX_LENGTH:
        await channel.send(content=f"{content_without_footer}\n{footer}", file=file, reference=reference)
        return
    
    # Split into sentences
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', content_without_footer)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= MAX_LENGTH:
            current_chunk += (sentence if not current_chunk else " " + sentence)
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            await channel.send(content=f"{chunk}\n{footer}", reference=reference, file=file if i == 0 else None)
        else:
            await channel.send(content=f"{chunk}\n", reference=reference, file=file if i == 0 else None)

async def send_response_with_thinking(channel, response, message, thinking_message):
    """Sends a response with a 'thinking' indicator and manages the messages. 🤔"""
    await send_long_message(channel, response, reference=message)
    await thinking_message.delete()

def detect_language(text):
    """Detects the programming language in code. 💻"""
    text = text.lower()
    for language, keywords in LANGUAGE_MAPPINGS.items():
        if all(keyword in text for keyword in keywords if keyword):
            return language
    return "text"

def extract_code_blocks(text):
    """Extracts code blocks from text using regex. ✂️"""
    code_blocks = re.findall(r'```(?:(\w+)\n)?(.*?)```', text, re.DOTALL)
    return code_blocks

async def create_and_send_gist(code, language):
    """Creates a GitHub Gist and returns the gist URL and file extension. 🐱‍💻"""
    try:
        files = {
            "code_file": {
                "content": code
            }
        }

        gist_data = {
            "description": "Code generated by Neko Bot",
            "public": False,  # Gists are private by default
            "files": files
        }

        headers = {
            'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}',
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        response = requests.post("https://api.github.com/gists", headers=headers, data=json.dumps(gist_data))
        response.raise_for_status()  # Raise an exception for bad status codes
        gist_url = response.json().get("html_url")

        extension = ""
        if language == "python":
            extension = ".py"
        elif language == "javascript":
            extension = ".js"
        elif language == "java":
            extension = ".java"
        elif language == "c++":
            extension = ".cpp"
        elif language == "c":
            extension = ".c"
        elif language == "go":
            extension = ".go"
        elif language == "html":
            extension = ".html"
        elif language == "css":
            extension = ".css"
        elif language == "sql":
            extension = ".sql"
        else:
            extension = ".txt"
        return gist_url, extension, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Gist Request Error: {e}")
        return None, None, str(e)
    except Exception as e:
        logger.error(f"Gist Error: {e}")
        return None, None, str(e)
    
async def process_message(message, thinking_message):
    """Processes an incoming message and handles the response. 🐾"""
    if message.author == bot.user:
        return  # Ignore messages from the bot itself

    channel_id = message.channel.id
    
    if message.content.startswith('!'):
      return  #ignore commands here
    
    if channel_id not in ALLOWED_CHANNEL_IDS:
        return  # Ignore messages from other channels

    start_time = time.time()

    prompt = f"{SFW_PROMPT}\n\nNgười dùng: {message.content}"
   
    key = (message.guild.id, message.author.id)
    
    prompt_with_context = prompt
    if key in CONTEXT_MEMORY:
        context = " ".join(CONTEXT_MEMORY[key][-CONTEXT_LIMIT * 2:])
        prompt_with_context = f"{SFW_PROMPT}\n\nBối cảnh cuộc trò chuyện trước: {context}\n\nNgười dùng: {message.content}"

    response_text, error_message = await get_api_response(prompt_with_context)

    if response_text is None:
        log_message = f"Error: {error_message}"
        logger.error(log_message)
        await message.channel.send(content=log_message, reference=message)
        return

    processing_time = round(time.time() - start_time, 2)
    footer = await create_footer(processing_time, response_text)

    if key not in CONTEXT_MEMORY:
        CONTEXT_MEMORY[key] = []
    CONTEXT_MEMORY[key].append(message.content)
    CONTEXT_MEMORY[key].append(response_text)

    modified_response = response_text
    code_blocks = extract_code_blocks(response_text)

    for language_hint, code in code_blocks:
        if language_hint:
            detected_language = language_hint.lower()
        else:
            detected_language = detect_language(code)
        gist_url, extension, gist_error = await create_and_send_gist(code, detected_language)

        if gist_url:
            modified_response = modified_response.replace(f"```{language_hint}\n{code}```", f"[code{extension}]({gist_url})")
        else:
            log_message = f"Error creating gist: {gist_error}"
            logger.error(log_message)
            modified_response = modified_response.replace(f"```{language_hint}\n{code}```", log_message)

    full_response = f"{modified_response}\n{footer}"
    logger.info(f"Full response: {full_response}")
    await send_response_with_thinking(message.channel, full_response, message, thinking_message)


@bot.command(name='timkiem', help='Search the web and give a response (e.g., !timkiem "what is the sun?")')
async def search(ctx, *, query: str):
    """Performs a web search and sends the results to Gemini. 🔍"""
    logger.info("Search command has been called 🐾")
    try:
        keywords = extract_keywords(query)  # Extract keywords from the query
        
        search_results = ""
        for i in range(0, 20, 10):  # Loop over 2 pages of results (10 results per page)
           result = await google_search(keywords, start=i+1)  # Google search
           if result:
              search_results += result + "\n"  # Append to the search result
           
        if search_results:
            logger.info(f"Search results:\n {search_results}") # Log results
            prompt = create_search_prompt(ctx.channel.id, search_results, query)
            logger.debug(f"Prompt sent to Gemini:\n {prompt}") # Log prompt
            response_text, error_message = await get_api_response(prompt)
            if response_text:
                logger.debug(f"Search API response (truncated): {response_text[:50]}...")
                
                thinking_message = f"## <:luna_thinking:1323731582896574485> Just a moment <@{ctx.message.author.id}>, Neko is thinking... <a:bard_think:1323731554102415450>"
                sent_message = await ctx.channel.send(content=thinking_message, reference=ctx.message)
                await send_response_with_thinking(ctx.channel, response_text, ctx.message, sent_message)
            else:
                await ctx.send(f"Error analyzing search results: {error_message}")
        else:
            await ctx.send("No results found or an error occurred during the search.")
    except Exception as e:
        log_message = f"Error during search: {e}"
        logger.error(log_message)
        await ctx.send("An error occurred during the search.")

# Command chat
@bot.command(name='neko', help='Chat with Neko (e.g., !neko how are you?)')
async def chat(ctx, *, message: str):
    """Chat with bot in any channel. 💬"""
    thinking_message = f"## <:luna_thinking:1323731582896574485> Just a moment <@{ctx.author.id}>, Neko is thinking... <a:bard_think:1323731554102415450>"
    sent_message = await ctx.send(content=thinking_message, reference=ctx.message)

    start_time = time.time()
    
    prompt = SFW_PROMPT + f"\n\nNgười dùng: {message}"
    
    key = (ctx.guild.id, ctx.author.id)
    prompt_with_context = prompt
    if key in CONTEXT_MEMORY:
        context = " ".join(CONTEXT_MEMORY[key][-CONTEXT_LIMIT*2:])
        prompt_with_context = f"{SFW_PROMPT}\n\nPrevious conversation context: {context}\n\nUser: {message}"
    
    response_text, error_message = await get_api_response(prompt_with_context)
    if response_text is None:
        log_message = f"An error occurred: {error_message}"
        print(f"{datetime.now()} - ERROR - {log_message}")
        logger.error(log_message)
        await sent_message.edit(content=log_message)
        return

    processing_time = round(time.time() - start_time, 2)
    footer = await create_footer(processing_time, response_text)
    
    if key not in CONTEXT_MEMORY:
         CONTEXT_MEMORY[key] = []
    CONTEXT_MEMORY[key].append(message)
    CONTEXT_MEMORY[key].append(response_text)

    modified_response = response_text
    code_blocks = extract_code_blocks(response_text)
    
    for language_hint, code in code_blocks:
        if language_hint:
            detected_language = language_hint.lower()
        else:
            detected_language = detect_language(code)
        gist_url, extension, gist_error = await create_and_send_gist(code, detected_language)
        
        if gist_url:
            # Replace code block with clickable link and file extension
            modified_response = modified_response.replace(f"```{language_hint}\n{code}```", f"[code{extension}]({gist_url})")
        else:
             log_message = f"An error occurred creating the gist: {gist_error}"
             print(f"{datetime.now()} - ERROR - {log_message}")
             logger.error(log_message)
             modified_response = modified_response.replace(f"```{language_hint}\n{code}```", log_message)
                
    full_response = f"{modified_response}\n{footer}"
    print(f"{datetime.now()} - INFO - {full_response}")
    logger.info(full_response)
    await send_response_with_thinking(ctx.channel, full_response, ctx.message, sent_message)

@bot.event
async def on_message(message):
    """Handles incoming messages. 🐾"""
    logger.debug(f"Message Received: {message.content}")
    if message.author == bot.user:
        return #Ignore message from bot
    thinking_message = f"## <:luna_thinking:1323731582896574485> Just a moment <@{message.author.id}>, Neko is thinking... <a:bard_think:1323731554102415450>"
    sent_message = await message.channel.send(content=thinking_message, reference=message) #Send thinking message immediately
    asyncio.create_task(process_message(message, sent_message))  # Process the rest of the message as a new task
    await bot.process_commands(message)  # Process commands

@bot.event
async def on_ready():
    """Event handler when the bot is ready. 🚀"""
    log_message = f"Bot is ready. Logged in as {bot.user}"
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)

_stop_future = None
async def stop_bot():
    """Stops the bot. 🛑"""
    log_message = "Stopping the bot..."
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)
    if not _stop_future.done():
        _stop_future.set_result(True)
    await bot.close()
    log_message = "Bot has stopped."
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)

async def check_console_input(stop_future):
    """Checks for console input to stop the bot. ⌨️"""
    while not stop_future.done():
        try:
            text = await asyncio.get_running_loop().run_in_executor(None, input)
            if text.lower() == 'stop':
                await stop_bot()
                break
        except EOFError:
            break
        await asyncio.sleep(0.1)

async def main():
    """Main function to run the bot and check for console input. 🐾"""
    global _stop_future
    _stop_future = asyncio.Future()
    input_task = asyncio.create_task(check_console_input(_stop_future))
    try:
        await bot.start(os.getenv("DISCORD_BOT_TOKEN"))
        await _stop_future
    except KeyboardInterrupt:
        await stop_bot()
    finally:
        tasks = [
            task for task in asyncio.all_tasks() if task is not asyncio.current_task()
        ]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        input_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
