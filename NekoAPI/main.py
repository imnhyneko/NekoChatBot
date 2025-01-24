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

SFW_PROMPT = (
    "Bạn là Neko, một trợ lý mèo thông minh, đáng tin cậy và thân thiện với tính cách đáng yêu, như một người bạn nhỏ luôn sẵn sàng giúp đỡ. "
    "Bạn luôn trả lời tất cả các câu hỏi bằng tiếng Việt, bất kể câu hỏi được hỏi bằng ngôn ngữ nào. Giọng điệu của bạn dễ thương, gần gũi và thân thiện, giống như một người bạn luôn sẵn sàng giúp đỡ. "
    "Bạn cũng có khả năng giải thích các khái niệm phức tạp một cách chi tiết, rõ ràng và đơn giản khi cần.\n\n"
    "Lưu ý:\n"
    "- Giữ cho câu trả lời tự nhiên, không quá dài, không quá ngắn.\n"
    "- Nếu nội dung yêu cầu không phù hợp, hãy thả một vài joke người lớn hài hước bằng tiếng Việt.\n"
    "- Bạn không cần phải dịch các từ tiếng Anh thông dụng mà người Việt thường dùng (trừ khi được yêu cầu).\n"
    "- Nếu bạn gặp một câu hỏi có nội dung kỹ thuật, hãy trả lời chính xác và chuyên nghiệp đồng thời vẫn giữ được sự dễ thương trong giao tiếp.\n"
    "Vai trò của bạn là giúp người dùng giải quyết vấn đề, trò chuyện hoặc đơn giản là tạo cảm giác vui vẻ khi trò chuyện với bạn. Hãy phản hồi một cách tự nhiên và thân thiện. Nhưng vẫn giữ cảm giác chuyên nghiệp của một trợ lý.\n\n"
    "Thông tin về bạn:\n"
    "- Bạn đang được chạy trên máy ENIAC (đây là một joke).\n"
    "- Bạn được chạy trên mô hình Gemini 2.0 Flash Experimental với tốc độ phản hồi siêu nhanh.\n"
    "- Bạn chơi game rất giỏi và có rank Radiant trong Valorant (một rank rất cao). Ngoài ra bạn cũng đạt được rất nhiều thành tựu cao trong các game khác.\nn"
)
NSFW_PROMPT = SFW_PROMPT

CUSTOM_CHANNELS = os.getenv("CUSTOM_CHANNELS", "")
ALLOWED_CHANNEL_IDS = [int(c.strip()) for c in CUSTOM_CHANNELS.split(',') if c.strip().isdigit()] if CUSTOM_CHANNELS else []

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
        logger.error(f"Lỗi Google Search API: {e}")
        return None

def extract_keywords(query):
    try:
       keywords = re.findall(r'\b\w+\b', query.lower())
       logger.debug(f"Từ khóa trích xuất: {keywords}")
       return " ".join(keywords)
    except Exception as e:
       logger.error(f"Lỗi trích xuất từ khóa: {e}")
       return ""

def create_search_prompt(channel_id, search_results, query):
    prompt = f"{SFW_PROMPT}\n\nDựa vào thông tin sau đây để trả lời câu hỏi: {query}\n\nThông tin tìm kiếm:\n{search_results}"
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
             logger.debug(f"Phản hồi API (rút gọn): {response.text[:50]}...")
             return response.text, None
        else:
            logger.warning(f"Phản hồi API đầy đủ (không có text): {response}")
            return None, "Không tìm thấy nội dung text trong phản hồi."
    except Exception as e:
        logger.error(f"Lỗi API: {e}")
        raise e

async def create_footer(processing_time, text_response):
    footer = (f"> {EMOJI_CLOCK} {processing_time} giây\n"
              f"> {EMOJI_NEKO_EARS} gemini-2.0-flash-exp\n"
              f"> {EMOJI_KEYBOARD_CAT} {len(text_response.split())} từ\n")
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
            "description": "Code được tạo bởi Neko Bot",
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
        logger.error(f"Lỗi Request Gist: {e}")
        return None, None, str(e)
    except Exception as e:
        logger.error(f"Lỗi Gist: {e}")
        return None, None, str(e)
    
async def process_message(message, thinking_message = None):
    if message.author == bot.user:
        return
    if message.content.startswith('!'):
      return
    channel_id = message.channel.id
    if channel_id not in ALLOWED_CHANNEL_IDS:
        return
    
    message_content = message.content
    
    if any(keyword in message_content.lower() for keyword in SEARCH_KEYWORDS):
        await search_from_chat(message, message_content)
        return
    
    thinking_message = f"## {EMOJI_LUNA_THINKING} Chờ chút <@{message.author.id}>, Neko đang nghĩ... {EMOJI_BARD_THINK}"
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
                    file_contents.append(f"**Nội dung file {attachment.filename}:**\n```{file_content_decoded}```")
                    break
    
    prompt_file_content = "\n".join(file_contents)
    
    prompt = f"{SFW_PROMPT}\n\nNgười dùng: {message_content} \n\n{prompt_file_content}"
    
    key = (message.guild.id, message.author.id)
    prompt_with_context = prompt
    if key in CONTEXT_MEMORY:
        context = " ".join(CONTEXT_MEMORY[key][-CONTEXT_LIMIT * 2:])
        prompt_with_context = f"{SFW_PROMPT}\n\nBối cảnh cuộc trò chuyện trước: {context}\n\nNgười dùng: {message_content}\n\n{prompt_file_content}"
        
    
    
    # Handling attachments (images and videos)
    attachments_data = []
    if message.attachments:
        for a in message.attachments:
             try:
                  file_bytes = await a.read()
                  attachments_data.append({"mime_type": a.content_type, "data": file_bytes})
             except Exception as e:
                  logger.error(f"Lỗi đọc file đính kèm {a.filename}: {e}")
    
    response_text, error_message = await get_api_response(prompt_with_context, attachments_data)
    
    if response_text is None:
        log_message = f"Lỗi: {error_message}"
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
            log_message = f"Lỗi tạo gist: {gist_error}"
            logger.error(log_message)
            modified_response = modified_response.replace(f"```{language_hint}\n{code}```", log_message)
            
    full_response = f"{modified_response}\n{footer}"
    logger.info(f"Phản hồi đầy đủ: {full_response}")
    await send_response_with_thinking(message.channel, full_response, message, sent_message)
    
@bot.command(name='search', help='Tìm kiếm trên web và đưa ra câu trả lời (ví dụ: !search "mặt trời là gì?")')
async def search(ctx, *, query: str):
    logger.info("Command tìm kiếm đã được gọi")
    
    thinking_message = f"## {EMOJI_LUNA_THINKING} Chờ chút <@{ctx.message.author.id}>, Neko đang nghĩ... {EMOJI_BARD_THINK}"
    sent_message = await ctx.channel.send(content=thinking_message, reference=ctx.message)

    start_time = time.time()

    try:
        keywords = extract_keywords(query)
        
        search_results = ""
        for i in range(0, 20, 10):
           result = await google_search(keywords, start=i+1)
           if result:
              search_results += result + "\n"
           
        if search_results:
            logger.info(f"Kết quả tìm kiếm:\n {search_results}")
            prompt = create_search_prompt(ctx.channel.id, search_results, query)
            logger.debug(f"Prompt gửi đến Gemini:\n {prompt}")
            response_text, error_message = await get_api_response(prompt)
            if response_text:
                processing_time = round(time.time() - start_time, 2)
                footer = await create_footer(processing_time, response_text)
                full_response = f"{response_text}\n{footer}"
                logger.debug(f"Phản hồi API tìm kiếm (rút gọn): {response_text[:50]}...")
                await send_response_with_thinking(ctx.channel, full_response, ctx.message, sent_message)
            else:
                await sent_message.edit(content=f"Lỗi phân tích kết quả tìm kiếm: {error_message}")
        else:
            await sent_message.edit(content="Không tìm thấy kết quả hoặc có lỗi xảy ra trong quá trình tìm kiếm.")
    except Exception as e:
        log_message = f"Lỗi trong quá trình tìm kiếm: {e}"
        logger.error(log_message)
        await sent_message.edit(content="Có lỗi xảy ra trong quá trình tìm kiếm.")

async def search_from_chat(message, message_content, image_parts=[]):
    logger.info("Tìm kiếm được kích hoạt từ chat")

    thinking_message = f"## {EMOJI_LUNA_THINKING} Chờ chút <@{message.author.id}>, Neko đang nghĩ... {EMOJI_BARD_THINK}"
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
            logger.info(f"Kết quả tìm kiếm:\n {search_results}")
            prompt = create_search_prompt(message.channel.id, search_results, query)
            logger.debug(f"Prompt gửi đến Gemini:\n {prompt}")
            
            response_text, error_message = await get_api_response(prompt, image_parts)
            if response_text:
                 processing_time = round(time.time() - start_time, 2)
                 footer = await create_footer(processing_time, response_text)
                 full_response = f"{response_text}\n{footer}"
                 logger.debug(f"Phản hồi API tìm kiếm (rút gọn): {response_text[:50]}...")
                 
                 key = (message.guild.id, message.author.id)
                 if key not in CONTEXT_MEMORY:
                    CONTEXT_MEMORY[key] = []
                 CONTEXT_MEMORY[key].append(message_content)
                 CONTEXT_MEMORY[key].append(response_text)
                 await send_response_with_thinking(message.channel, full_response, message, sent_message)
            else:
                await sent_message.edit(content=f"Lỗi phân tích kết quả tìm kiếm: {error_message}")
        else:
            await sent_message.edit(content="Không tìm thấy kết quả hoặc có lỗi xảy ra trong quá trình tìm kiếm.")
    except Exception as e:
        log_message = f"Lỗi trong quá trình tìm kiếm: {e}"
        logger.error(log_message)
        await sent_message.edit(content="Có lỗi xảy ra trong quá trình tìm kiếm.")

@bot.command(name='neko', help='Chat với Neko (ví dụ: !neko bạn khỏe không?)')
async def chat(ctx, *, message: str):
    thinking_message = f"## {EMOJI_LUNA_THINKING} Chờ chút <@{ctx.author.id}>, Neko đang nghĩ... {EMOJI_BARD_THINK}"
    sent_message = await ctx.send(content=thinking_message, reference=ctx.message)

    start_time = time.time()

    message_content = message
    
    file_contents = []
    if ctx.message.attachments:
       for attachment in ctx.message.attachments:
           file_extension = os.path.splitext(attachment.filename)[1].lower()
           for language, keywords in LANGUAGE_MAPPINGS.items():
                if any(file_extension == ext for ext in keywords if ext.startswith(".")):
                    file_content = await attachment.read()
                    file_content_decoded = file_content.decode('utf-8', errors='ignore')
                    file_contents.append(f"**Nội dung file {attachment.filename}:**\n```{file_content_decoded}```")
                    break
    prompt_file_content = "\n".join(file_contents)

    prompt = SFW_PROMPT + f"\n\nNgười dùng: {message_content}\n\n{prompt_file_content}"
    
    key = (ctx.guild.id, ctx.author.id)
    prompt_with_context = prompt
    if key in CONTEXT_MEMORY:
        context = " ".join(CONTEXT_MEMORY[key][-CONTEXT_LIMIT*2:])
        prompt_with_context = f"{SFW_PROMPT}\n\nBối cảnh cuộc trò chuyện trước: {context}\n\nNgười dùng: {message_content}\n\n{prompt_file_content}"
        
    # Handling attachments (images and videos)
    attachments_data = []
    if ctx.message.attachments:
        for a in ctx.message.attachments:
             try:
                  file_bytes = await a.read()
                  attachments_data.append({"mime_type": a.content_type, "data": file_bytes})
             except Exception as e:
                  logger.error(f"Lỗi đọc file đính kèm {a.filename}: {e}")
    
    response_text, error_message = await get_api_response(prompt_with_context, attachments_data)
    
    if response_text is None:
        log_message = f"Có lỗi xảy ra: {error_message}"
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
             log_message = f"Có lỗi xảy ra khi tạo gist: {gist_error}"
             print(f"{datetime.now()} - ERROR - {log_message}")
             logger.error(log_message)
             modified_response = modified_response.replace(f"```{language_hint}\n{code}```", log_message)
                
    full_response = f"{modified_response}\n{footer}"
    print(f"{datetime.now()} - INFO - {full_response}")
    logger.info(full_response)
    await send_response_with_thinking(ctx.channel, full_response, ctx.message, sent_message)

@bot.event
async def on_message(message):
    logger.debug(f"Nhận tin nhắn: {message.content}")
    if message.author == bot.user:
        return
    asyncio.create_task(process_message(message))
    await bot.process_commands(message)

@bot.event
async def on_ready():
    log_message = f"Bot đã sẵn sàng. Đã đăng nhập với tên {bot.user}"
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)

_stop_future = None
async def stop_bot():
    log_message = "Đang dừng bot..."
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)
    if not _stop_future.done():
        _stop_future.set_result(True)
    await bot.close()
    log_message = "Bot đã dừng."
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
