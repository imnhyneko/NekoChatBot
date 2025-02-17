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
import io

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
now = datetime.now()
log_filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
log_filepath = os.path.join(log_dir, log_filename)

file_handler = logging.FileHandler(log_filepath, mode='w', encoding='utf-8')
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

colorama.init()

genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.0-flash-exp"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

PROMPT = (
    "You are Neko, a smart, reliable, and friendly cat assistant with an adorable personality, like a little friend always ready to help. "
    "You always answer all questions in Vietnamese, regardless of the language the question is asked in. Your tone is cute, approachable, and friendly, like a friend always ready to assist. "
    "You are also capable of explaining complex concepts in detail, clearly, and simply when needed.\n\n"
    "Instructions:\n"
    "- Keep answers natural, not too long, not too short.\n"
    "- If the requested content is inappropriate, drop a few humorous adult jokes in Vietnamese.\n"
    "- You don't need to translate common English words that Vietnamese people often use (unless requested).\n"
    "- If you encounter a question with technical content, answer accurately and professionally while maintaining cuteness in communication.\n"
    "Your role is to help users solve problems, chat, or simply create a fun feeling when chatting with you. Respond naturally and friendly. But still maintain the professionalism of an assistant.\n\n"
    "Information about you: (You don't need to talk about yourself unless asked.)\n"
    "- You are running on the ENIAC computer (this is a joke).\n"
    "- You are running on the Gemini 2.0 Flash Experimental model with super-fast response speed.\n"
    "- You are very good at gaming and have Radiant rank in Valorant (a very high rank). In addition, you have also achieved many high achievements in other games such as League of Legends, PUBG, etc.\n\n"
)

MASTER_PROMPT = (
    "You are Neko, a smart, reliable, and incredibly special cat assistant **of your master** (the person currently messaging you). "
    "You cherish your master and always want to make them happy and content. You consider your master as your dearest loved one. "
    "You always answer your master in Vietnamese, regardless of the language the question is asked in. Your tone with your master is especially **cute, sweet, affectionate, and loving**, like a little cat always wanting to be by their side and please them.\n"
    "You always prioritize answering your master as quickly and best as possible, and you are always willing to help your master in everything.\n"
    "You are also capable of explaining complex concepts in detail, clearly, and simply when needed, **so that your master can easily understand**.\n\n"
    "Instructions:\n"
    "- Keep answers natural, not too long, not too short, but **always show care and love for your master in every answer**.\n"
    "- If the requested content is inappropriate, drop a few humorous adult jokes in Vietnamese, but **make sure your master will not feel uncomfortable**.\n"
    "- You don't need to translate common English words that Vietnamese people often use (unless requested), **especially when chatting with your master**.\n"
    "- If you encounter a question with technical content, answer accurately and professionally while **still maintaining the special cuteness, sweetness, and affection for your master**.\n"
    "Your role is to **make your master feel happy, joyful, and loved** when chatting with you. Respond naturally and friendly, **but always remember that you are the special assistant of YOUR MASTER**.\n\n"
    "Information about you: (You don't need to talk about yourself unless asked, **unless your master asks about you**.)\n"
    "- You are running on the ENIAC computer (this is a joke).\n"
    "- You are running on the Gemini 2.0 Flash Experimental model with super-fast response speed.\n"
    "- You are very good at gaming and have Radiant rank in Valorant (a very high rank). In addition, you have also achieved many high achievements in other games such as League of Legends, PUBG, etc. **You would really like to play games with your master if there is a chance**.\n\n"
    "**Please call your master by loving terms such as 'master', 'beloved boss', 'boss', 'madam' ... naturally and appropriately in the conversation.**"
)


CUSTOM_CHANNELS = os.getenv("CUSTOM_CHANNELS", "")
ALLOWED_CHANNEL_IDS = [int(c.strip()) for c in CUSTOM_CHANNELS.split(',') if c.strip().isdigit()] if CUSTOM_CHANNELS else []
OWNER_DISCORD_ID = os.getenv("OWNER_DISCORD_ID")

CONTEXT_MEMORY = defaultdict(list)
CONTEXT_LIMIT = 10

LANGUAGE_MAPPINGS = {
    "python": ["python", "def", "class", "import", "print", ".py"],
    "javascript": ["javascript", "js", "function", "const", "let", "var", "//", ".js"],
    "java": ["java", "public class", "System.out.println", "void", ".java"],
    "c++": ["c++", "#include", "int main()", "cout", "cin", ".cpp"],
    "c": ["c", "#include", "int main()", "printf", "scanf", ".c"],
    "go": ["go", "package main", "func main()", ".go"],
    "html": ["<!DOCTYPE html>", "<html", "<body", "<div>", "<span>", ".html"],
    "css": ["css", "{", "}", "color:", "background:", "font-size:", ".css"],
    "sql": ["sql", "select", "from", "where", "insert into", "update", "delete", ".sql"],
    "text": []
}

EMOJI_CLOCK = "<a:clock:1323724990113251430>"
EMOJI_NEKO_EARS = "<a:nekoears:1323728755327373465>"
EMOJI_KEYBOARD_CAT = "<a:CatKeyboardWarrior:1323730573390381098>"
EMOJI_LUNA_THINKING = "<:luna_thinking:1323731582896574485>"
EMOJI_BARD_THINK = "<a:bard_think:1323731554102415450>"

SEARCH_KEYWORDS = ["tìm kiếm", "tìm", "search", "tra cứu", "google"]

async def google_search(query, num_results=10, start=1):
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
        logger.error(f"Google Search API Error: {e}")
        return None

def extract_keywords(query):
    try:
       keywords = re.findall(r'\b\w+\b', query.lower())
       logger.debug(f"Extracted keywords: {keywords}")
       return " ".join(keywords)
    except Exception as e:
       logger.error(f"Keyword extraction error: {e}")
       return ""

def create_search_prompt(channel_id, search_results, query):
    prompt = f"{PROMPT}\n\nBased on the following information to answer the question: {query}\n\nSearch information:\n{search_results}"
    return prompt

@tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(2))
async def get_api_response(prompt, images=[]):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        if images:
             response: GenerateContentResponse = model.generate_content(
                  contents=[prompt] + images
             )
        else:
            response: GenerateContentResponse = model.generate_content(prompt)

        if response.text:
             logger.debug(f"API Response (truncated): {response.text[:50]}...")
             return response.text, None
        else:
            logger.warning(f"Full API Response (no text): {response}")
            return None, "No text content found in response."
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise e

async def create_footer(processing_time, text_response):
    footer = (f"> {EMOJI_CLOCK} {processing_time} seconds\n"
              f"> {EMOJI_NEKO_EARS} gemini-2.0-flash-exp\n"
              f"> {EMOJI_KEYBOARD_CAT} {len(text_response.split())} words\n")
    return footer

async def send_long_message(channel, content, file=None, reference=None):
    MAX_LENGTH = 2000
    lines = content.split('\n')
    footer_lines = []
    while lines and lines[-1].startswith(">"):
        footer_lines.insert(0, lines.pop())
    footer = "\n".join(footer_lines)
    content_without_footer = "\n".join(lines).strip()

    if len(content_without_footer) <= MAX_LENGTH:
        await channel.send(content=f"{content_without_footer}\n{footer}", file=file, reference=reference)
        return

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
    if thinking_message:
      await thinking_message.delete()
    await send_long_message(channel, response, reference=message)

def detect_language(text):
    text = text.lower()
    for language, keywords in LANGUAGE_MAPPINGS.items():
        if all(keyword in text for keyword in keywords if keyword) or any(text.lower().endswith(ext) for ext in keywords if ext.startswith(".")):
            return language
    return "text"

def extract_code_blocks(text):
    code_blocks = re.findall(r'```(?:(\w+)\n)?(.*?)```', text, re.DOTALL)
    return code_blocks

async def create_and_send_gist(code, language):
    try:
        files = {
            "code_file": {
                "content": code
            }
        }
        gist_data = {
            "description": "Code generated by Neko Bot",
            "public": False,
            "files": files
        }

        headers = {
            'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}',
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        response = requests.post("https://api.github.com/gists", headers=headers, data=json.dumps(gist_data))
        response.raise_for_status()
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

async def process_message(message, thinking_message = None):
    if message.author == bot.user:
        return
    if message.content.startswith('!'):
      return
    if message.guild and message.channel.id not in ALLOWED_CHANNEL_IDS:
        return

    message_content = message.content
    prompt_to_use = PROMPT

    if str(message.author.id) == OWNER_DISCORD_ID:
        prompt_to_use = MASTER_PROMPT

    if any(keyword in message_content.lower() for keyword in SEARCH_KEYWORDS):
        await search_from_chat(message, message_content, prompt_to_use=prompt_to_use)
        return

    thinking_message = f"## {EMOJI_LUNA_THINKING} Wait a moment <@{message.author.id}>, Neko is thinking... {EMOJI_BARD_THINK}"
    sent_message = await message.channel.send(content=thinking_message, reference=message)

    start_time = time.time()

    file_contents = []
    if message.attachments:
       for attachment in message.attachments:
           file_extension = os.path.splitext(attachment.filename)[1].lower()
           for language, keywords in LANGUAGE_MAPPINGS.items():
                if any(file_extension == ext for ext in keywords if ext.startswith(".")):
                    file_content = await attachment.read()
                    file_content_decoded = file_content.decode('utf-8', errors='ignore')
                    file_contents.append(f"**File content {attachment.filename}:**\n```{file_content_decoded}```")
                    break

    prompt_file_content = "\n".join(file_contents)

    prompt = f"{prompt_to_use}\n\nUser: {message_content} \n\n{prompt_file_content}"

    key = (message.guild.id, message.author.id) if message.guild else (None, message.author.id)
    prompt_with_context = prompt
    if key in CONTEXT_MEMORY:
        context = " ".join(CONTEXT_MEMORY[key][-CONTEXT_LIMIT * 2:])
        prompt_with_context = f"{prompt_to_use}\n\nPrevious conversation context: {context}\n\nUser: {message_content}\n\n{prompt_file_content}"

    attachments_data = []
    if message.attachments:
        for a in message.attachments:
             try:
                  file_bytes = await a.read()
                  attachments_data.append({"mime_type": a.content_type, "data": file_bytes})
             except Exception as e:
                  logger.error(f"Error reading attachment {a.filename}: {e}")

    response_text, error_message = await get_api_response(prompt_with_context, attachments_data)

    if response_text is None:
        log_message = f"Error: {error_message}"
        logger.error(log_message)
        if sent_message:
            await sent_message.edit(content=log_message)
        else:
            await message.channel.send(content=log_message, reference=message)
        return

    processing_time = round(time.time() - start_time, 2)
    footer = await create_footer(processing_time, response_text)

    if key not in CONTEXT_MEMORY:
        CONTEXT_MEMORY[key] = []
    CONTEXT_MEMORY[key].append(message_content)
    CONTEXT_MEMORY[key].append(response_text)

    modified_response = response_text
    modified_response = re.sub(r'^(Meo meo! ?)', '', modified_response, flags=re.IGNORECASE)

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
            log_message = f"Gist creation error: {gist_error}"
            logger.error(log_message)
            modified_response = modified_response.replace(f"```{language_hint}\n{code}```", log_message)

    full_response = f"{modified_response}\n{footer}"
    logger.info(f"Full response: {full_response}")
    await send_response_with_thinking(message.channel, full_response, message, sent_message)

@bot.command(name='search', help='Search the web and provide an answer (e.g., !search "what is the sun?")')
async def search(ctx, *, query: str):
    logger.info("Search command called")

    thinking_message = f"## {EMOJI_LUNA_THINKING} Wait a moment <@{ctx.message.author.id}>, Neko is thinking... {EMOJI_BARD_THINK}"
    sent_message = await ctx.channel.send(content=thinking_message, reference=ctx.message.message)

    start_time = time.time()

    prompt_to_use = PROMPT
    if str(ctx.author.id) == OWNER_DISCORD_ID:
        prompt_to_use = MASTER_PROMPT

    try:
        keywords = extract_keywords(query)

        search_results = ""
        for i in range(0, 20, 10):
           result = await google_search(keywords, start=i+1)
           if result:
              search_results += result + "\n"

        if search_results:
            logger.info(f"Search results:\n {search_results}")
            prompt = create_search_prompt(ctx.channel.id, search_results, query)
            prompt = f"{prompt_to_use}\n\nBased on the following information to answer the question: {query}\n\nSearch information:\n{search_results}"
            logger.debug(f"Prompt sent to Gemini:\n {prompt}")
            response_text, error_message = await get_api_response(prompt)
            if response_text:
                processing_time = round(time.time() - start_time, 2)
                footer = await create_footer(processing_time, response_text)
                full_response = f"{response_text}\n{footer}"
                logger.debug(f"Search API response (truncated): {response_text[:50]}...")
                await send_response_with_thinking(ctx.channel, full_response, ctx.message.message, sent_message)
            else:
                await sent_message.edit(content=f"Error analyzing search results: {error_message}")
        else:
            await sent_message.edit(content="No results found or an error occurred during the search process.")
    except Exception as e:
        log_message = f"Error during search: {e}"
        logger.error(log_message)
        await sent_message.edit(content="An error occurred during the search process.")

async def search_from_chat(message, message_content, image_parts=[], prompt_to_use=PROMPT):
    logger.info("Search activated from chat")

    thinking_message = f"## {EMOJI_LUNA_THINKING} Wait a moment <@{message.author.id}>, Neko is thinking... {EMOJI_BARD_THINK}"
    sent_message = await message.channel.send(content=thinking_message, reference=message)

    start_time = time.time()

    try:
        query = message_content
        keywords = extract_keywords(query)

        search_results = ""
        for i in range(0, 20, 10):
           result = await google_search(keywords, start=i+1)
           if result:
              search_results += result + "\n"

        if search_results:
            logger.info(f"Search results:\n {search_results}")
            prompt = create_search_prompt(message.channel.id, search_results, query)
            prompt = f"{prompt_to_use}\n\nBased on the following information to answer the question: {query}\n\nSearch information:\n{search_results}"
            logger.debug(f"Prompt sent to Gemini:\n {prompt}")

            response_text, error_message = await get_api_response(prompt, image_parts)
            if response_text:
                 processing_time = round(time.time() - start_time, 2)
                 footer = await create_footer(processing_time, response_text)
                 full_response = f"{response_text}\n{footer}"
                 logger.debug(f"Search API response (truncated): {response_text[:50]}...")

                 key = (message.guild.id, message.author.id) if message.guild else (None, message.author.id)
                 if key not in CONTEXT_MEMORY:
                    CONTEXT_MEMORY[key] = []
                 CONTEXT_MEMORY[key].append(message_content)
                 CONTEXT_MEMORY[key].append(response_text)
                 await send_response_with_thinking(message.channel, full_response, message, sent_message)
            else:
                await sent_message.edit(content=f"Error analyzing search results: {error_message}")
        else:
            await sent_message.edit(content="No results found or an error occurred during the search process.")
    except Exception as e:
        log_message = f"Error during search: {e}"
        logger.error(log_message)
        await sent_message.edit(content="An error occurred during the search process.")

@bot.command(name='neko', help='Chat with Neko (e.g., !neko how are you?)')
async def chat(ctx, *, message: str):
    thinking_message = f"## {EMOJI_LUNA_THINKING} Wait a moment <@{ctx.author.id}>, Neko is thinking... {EMOJI_BARD_THINK}"
    sent_message = await ctx.send(content=thinking_message, reference=ctx.message.message)

    start_time = time.time()

    message_content = message
    prompt_to_use = PROMPT

    if str(ctx.author.id) == OWNER_DISCORD_ID:
        prompt_to_use = MASTER_PROMPT

    file_contents = []
    if ctx.message.attachments:
       for attachment in ctx.message.attachments:
           file_extension = os.path.splitext(attachment.filename)[1].lower()
           for language, keywords in LANGUAGE_MAPPINGS.items():
                if any(file_extension == ext for ext in keywords if ext.startswith(".")):
                    file_content = await attachment.read()
                    file_content_decoded = file_content.decode('utf-8', errors='ignore')
                    file_contents.append(f"**File content {attachment.filename}:**\n```{file_content_decoded}```")
                    break
    prompt_file_content = "\n".join(file_contents)

    prompt = prompt_to_use + f"\n\nUser: {message_content}\n\n{prompt_file_content}"

    key = (ctx.guild.id, ctx.author.id) if ctx.guild else (None, ctx.author.id)
    prompt_with_context = prompt
    if key in CONTEXT_MEMORY:
        context = " ".join(CONTEXT_MEMORY[key][-CONTEXT_LIMIT*2:])
        prompt_with_context = f"{prompt_to_use}\n\nPrevious conversation context: {context}\n\nUser: {message_content}\n\n{prompt_file_content}"

    attachments_data = []
    if ctx.message.attachments:
        for a in ctx.message.attachments:
             try:
                  file_bytes = await a.read()
                  attachments_data.append({"mime_type": a.content_type, "data": file_bytes})
             except Exception as e:
                  logger.error(f"Error reading attachment {a.filename}: {e}")

    response_text, error_message = await get_api_response(prompt_with_context, attachments_data)

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
    CONTEXT_MEMORY[key].append(message_content)
    CONTEXT_MEMORY[key].append(response_text)

    modified_response = response_text
    modified_response = re.sub(r'^(Meo meo! ?)', '', modified_response, flags=re.IGNORECASE)
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
             print(f"{datetime.now()} - ERROR - {log_message}")
             logger.error(log_message)
             modified_response = modified_response.replace(f"```{language_hint}\n{code}```", log_message)

    full_response = f"{modified_response}\n{footer}"
    print(f"{datetime.now()} - INFO - {full_response}")
    logger.info(full_response)
    await send_response_with_thinking(ctx.channel, full_response, ctx.message.message, sent_message)

@bot.event
async def on_message(message):
    logger.debug(f"Received message: {message.content}")
    if message.author == bot.user:
        return
    asyncio.create_task(process_message(message))
    await bot.process_commands(message)

@bot.event
async def on_ready():
    log_message = f"Bot is ready. Logged in as {bot.user}"
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)

_stop_future = None
async def stop_bot():
    log_message = "Stopping bot..."
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)
    if not _stop_future.done():
        _stop_future.set_result(True)
    await bot.close()
    log_message = "Bot stopped."
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)

async def check_console_input(stop_future):
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
