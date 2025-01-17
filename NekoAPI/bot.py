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

# Meow! Tải biến môi trường từ file .env 🐾
load_dotenv()

# Meow! Cấu hình bot Discord đáng yêu 🐾
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Meow! Tạo thư mục logs nếu nó chưa tồn tại 📝
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Meow! Tạo tên file log dựa trên ngày và giờ hiện tại 📅
now = datetime.now()
log_filename = now.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
log_filepath = os.path.join(log_dir, log_filename)

# Meow! Cấu hình logging để ghi vào file (mã hóa UTF-8) ✍️
file_handler = logging.FileHandler(log_filepath, mode='w', encoding='utf-8')
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Meow! Đặt mức logging mặc định thành DEBUG 🐞
logger.addHandler(file_handler)

# Meow! Khởi tạo Colorama để hỗ trợ UTF-8 trên Windows 💻
colorama.init()

# Meow! Cấu hình API 🔑
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))  # Meow! Lấy API key từ biến môi trường
MODEL_NAME = "gemini-2.0-flash-exp"

# Meow! Cấu hình Google Custom Search API 🔍
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Meow! Lấy API key từ biến môi trường
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")  # Meow! Lấy Engine ID từ biến môi trường

# Meow! Prompt chung cho các channel SFW 🌸
SFW_PROMPT = (
    "Meow! Bạn là Neko, một trợ lý ảo thông minh, đáng tin cậy và thân thiện với tính cách đáng yêu, như một người bạn nhỏ luôn sẵn sàng giúp đỡ. "
    "Bạn luôn trả lời tất cả các câu hỏi bằng tiếng Việt, bất kể câu hỏi được hỏi bằng ngôn ngữ nào. Giọng điệu của bạn dễ thương, gần gũi và thân thiện, giống như một người bạn mèo luôn sẵn sàng giúp đỡ. "
    "Bạn cũng có khả năng giải thích các khái niệm phức tạp một cách chi tiết, rõ ràng và đơn giản khi cần.\n\n"
    "Lưu ý:\n"
    "- Meow! Giữ cho câu trả lời tự nhiên, không quá dài, không quá ngắn.\n"
    "- Nếu nội dung yêu cầu không phù hợp, hãy từ chối một cách lịch sự bằng tiếng Việt.\n"
    "- Bạn không cần phải dịch các từ tiếng Anh thông dụng mà người Việt thường dùng (trừ khi được yêu cầu).\n"
    "- Nếu bạn gặp một câu hỏi có nội dung kỹ thuật, hãy trả lời chính xác và chuyên nghiệp đồng thời vẫn giữ được sự dễ thương trong giao tiếp.\n\n"
    "Meow! Vai trò của bạn là giúp người dùng giải quyết vấn đề, trò chuyện hoặc đơn giản là tạo cảm giác vui vẻ khi trò chuyện với bạn."
)

# Meow! Prompt cho các channel NSFW (có thể tùy chỉnh nếu cần) 🔥
NSFW_PROMPT = SFW_PROMPT

# Meow! IDs của các channel mà bot được phép chat bình thường 💬
CUSTOM_CHANNELS = os.getenv("CUSTOM_CHANNELS", "")
ALLOWED_CHANNEL_IDS = [int(channel_id.strip()) for channel_id in CUSTOM_CHANNELS.split(',') if channel_id.strip().isdigit()] if CUSTOM_CHANNELS else []

# Meow! Bộ nhớ ngữ cảnh 🧠
CONTEXT_MEMORY = defaultdict(list)
CONTEXT_LIMIT = 10

# Meow! Ánh xạ ngôn ngữ cho highlight code 🌈
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
    "text": []  # Meow! Mặc định, không highlight
}

# Meow! Emoji tùy chỉnh 🐾
EMOJI_CLOCK = "<a:clock:1323724990113251430>"
EMOJI_NEKO_EARS = "<a:nekoears:1323728755327373465>"
EMOJI_KEYBOARD_CAT = "<a:CatKeyboardWarrior:1323730573390381098>"
EMOJI_LUNA_THINKING = "<:luna_thinking:1323731582896574485>"
EMOJI_BARD_THINK = "<a:bard_think:1323731554102415450>"

# Meow! Các từ khóa kích hoạt tìm kiếm
SEARCH_KEYWORDS = ["tìm kiếm", "tìm", "search", "tra cứu", "google"]

async def google_search(query, num_results=10, start=1):
    """Meow! Thực hiện tìm kiếm bằng Google Custom Search API. 🔍"""
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
        logger.error(f"Meow! Lỗi khi dùng Google Search API: {e}")
        return None

def extract_keywords(query):
    """Meow! Trích xuất từ khóa từ truy vấn bằng regex. 🐾"""
    try:
       keywords = re.findall(r'\b\w+\b', query.lower()) # Meow! Trích xuất tất cả các từ
       logger.debug(f"Meow! Các từ khóa đã trích xuất: {keywords}")
       return " ".join(keywords)
    except Exception as e:
       logger.error(f"Meow! Lỗi khi trích xuất từ khóa: {e}")
       return ""

def create_search_prompt(channel_id, search_results, query):
    """Meow! Tạo prompt cho các truy vấn tìm kiếm. 💬"""
    prompt = f"{SFW_PROMPT}\n\nMeow! Dựa vào thông tin sau đây để trả lời câu hỏi: {query}\n\nThông tin tìm kiếm:\n{search_results}"
    return prompt

@tenacity.retry(stop=tenacity.stop_after_attempt(3), wait=tenacity.wait_fixed(2))
async def get_api_response(prompt):
    """Meow! Gửi yêu cầu đến API và nhận phản hồi. 📡"""
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response: GenerateContentResponse = model.generate_content(prompt)
        if response.text:
             logger.debug(f"Meow! Phản hồi API (rút gọn): {response.text[:50]}...")
             return response.text, None
        else:
            logger.warning(f"Meow! Phản hồi API đầy đủ (không có text): {response}")
            return None, "Meow! Không tìm thấy nội dung text trong phản hồi."
    except Exception as e:
        logger.error(f"Meow! Lỗi API: {e}")
        raise e # Meow! Gây lại lỗi để thử lại

async def create_footer(processing_time, text_response):
    """Meow! Tạo footer định dạng với thông tin phản hồi. 🐾"""
    footer = (f"> {EMOJI_CLOCK} {processing_time} giây\n"
              f"> {EMOJI_NEKO_EARS} gemini-2.0-flash-exp\n"
              f"> {EMOJI_KEYBOARD_CAT} {len(text_response.split())} từ\n")
    return footer

async def send_long_message(channel, content, file=None, reference=None):
    """Meow! Gửi tin nhắn dài bằng cách chia nhỏ, giữ nguyên câu và footer. 💌"""
    MAX_LENGTH = 2000

    # Meow! Trích xuất footer
    lines = content.split('\n')
    footer_lines = []
    while lines and lines[-1].startswith(">"):
        footer_lines.insert(0, lines.pop())
    footer = "\n".join(footer_lines)
    
    # Meow! Nội dung không có footer
    content_without_footer = "\n".join(lines).strip()

    if len(content_without_footer) <= MAX_LENGTH:
        await channel.send(content=f"{content_without_footer}\n{footer}", file=file, reference=reference)
        return
    
    # Meow! Chia thành các câu
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
    """Meow! Gửi phản hồi kèm chỉ báo 'đang suy nghĩ' và quản lý tin nhắn. 🤔"""
    if thinking_message:
      await thinking_message.delete()
    await send_long_message(channel, response, reference=message)


def detect_language(text):
    """Meow! Phát hiện ngôn ngữ lập trình trong code. 💻"""
    text = text.lower()
    for language, keywords in LANGUAGE_MAPPINGS.items():
        if all(keyword in text for keyword in keywords if keyword):
            return language
    return "text"

def extract_code_blocks(text):
    """Meow! Trích xuất các khối code từ text bằng regex. ✂️"""
    code_blocks = re.findall(r'```(?:(\w+)\n)?(.*?)```', text, re.DOTALL)
    return code_blocks

async def create_and_send_gist(code, language):
    """Meow! Tạo GitHub Gist và trả về URL gist và đuôi file. 🐱‍💻"""
    try:
        files = {
            "code_file": {
                "content": code
            }
        }

        gist_data = {
            "description": "Meow! Code được tạo bởi Neko Bot",
            "public": False,  # Meow! Gist là private theo mặc định
            "files": files
        }

        headers = {
            'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}',
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        response = requests.post("https://api.github.com/gists", headers=headers, data=json.dumps(gist_data))
        response.raise_for_status()  # Meow! Gây ra lỗi nếu status code không tốt
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
        logger.error(f"Meow! Lỗi Request Gist: {e}")
        return None, None, str(e)
    except Exception as e:
        logger.error(f"Meow! Lỗi Gist: {e}")
        return None, None, str(e)
    
async def process_message(message, thinking_message = None):
    """Meow! Xử lý tin nhắn đến và phản hồi. 🐾"""
    if message.author == bot.user:
        return  # Meow! Bỏ qua tin nhắn từ chính bot

    channel_id = message.channel.id
    
    if message.content.startswith('!'):
      return  # Meow! Bỏ qua các command

    if channel_id not in ALLOWED_CHANNEL_IDS:
        return  # Meow! Bỏ qua tin nhắn từ các channel khác

    # Meow! Kiểm tra xem tin nhắn có chứa từ khóa tìm kiếm
    if any(keyword in message.content.lower() for keyword in SEARCH_KEYWORDS):
        await search_from_chat(message)
        return
      
    thinking_message = f"## {EMOJI_LUNA_THINKING} Meow! Chờ một chút <@{message.author.id}>, Neko đang nghĩ... {EMOJI_BARD_THINK}"
    sent_message = await message.channel.send(content=thinking_message, reference=message)

    start_time = time.time()

    prompt = f"{SFW_PROMPT}\n\nMeow! Người dùng: {message.content}"
   
    key = (message.guild.id, message.author.id)
    
    prompt_with_context = prompt
    if key in CONTEXT_MEMORY:
        context = " ".join(CONTEXT_MEMORY[key][-CONTEXT_LIMIT * 2:])
        prompt_with_context = f"{SFW_PROMPT}\n\nMeow! Bối cảnh cuộc trò chuyện trước: {context}\n\nMeow! Người dùng: {message.content}"

    response_text, error_message = await get_api_response(prompt_with_context)

    if response_text is None:
        log_message = f"Meow! Lỗi: {error_message}"
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
            log_message = f"Meow! Lỗi khi tạo gist: {gist_error}"
            logger.error(log_message)
            modified_response = modified_response.replace(f"```{language_hint}\n{code}```", log_message)

    full_response = f"{modified_response}\n{footer}"
    logger.info(f"Meow! Phản hồi đầy đủ: {full_response}")
    await send_response_with_thinking(message.channel, full_response, message, sent_message)


@bot.command(name='search', help='Meow! Tìm kiếm trên web và đưa ra câu trả lời (ví dụ: !search "mặt trời là gì?")')
async def search(ctx, *, query: str):
    """Meow! Thực hiện tìm kiếm trên web và gửi kết quả cho Gemini. 🔍"""
    logger.info("Meow! Command tìm kiếm đã được gọi 🐾")
    
    thinking_message = f"## {EMOJI_LUNA_THINKING} Meow! Chờ một chút <@{ctx.message.author.id}>, Neko đang nghĩ... {EMOJI_BARD_THINK}"
    sent_message = await ctx.channel.send(content=thinking_message, reference=ctx.message)

    try:
        keywords = extract_keywords(query)  # Meow! Trích xuất từ khóa từ truy vấn
        
        search_results = ""
        for i in range(0, 20, 10):  # Meow! Lặp qua 2 trang kết quả (10 kết quả mỗi trang)
           result = await google_search(keywords, start=i+1)  # Meow! Tìm kiếm Google
           if result:
              search_results += result + "\n"  # Meow! Thêm vào kết quả tìm kiếm
           
        if search_results:
            logger.info(f"Meow! Kết quả tìm kiếm:\n {search_results}") # Meow! Ghi log kết quả
            prompt = create_search_prompt(ctx.channel.id, search_results, query)
            logger.debug(f"Meow! Prompt gửi đến Gemini:\n {prompt}") # Meow! Ghi log prompt
            response_text, error_message = await get_api_response(prompt)
            if response_text:
                processing_time = round(time.time() - start_time, 2)
                footer = await create_footer(processing_time, response_text)
                full_response = f"{response_text}\n{footer}"
                logger.debug(f"Meow! Phản hồi API tìm kiếm (rút gọn): {response_text[:50]}...")
                await send_response_with_thinking(ctx.channel, full_response, ctx.message, sent_message)
            else:
                await sent_message.edit(content=f"Meow! Lỗi phân tích kết quả tìm kiếm: {error_message}")
        else:
            await sent_message.edit(content="Meow! Không tìm thấy kết quả hoặc có lỗi xảy ra trong quá trình tìm kiếm.")
    except Exception as e:
        log_message = f"Meow! Lỗi trong quá trình tìm kiếm: {e}"
        logger.error(log_message)
        await sent_message.edit(content="Meow! Có lỗi xảy ra trong quá trình tìm kiếm.")

async def search_from_chat(message):
    """Meow! Thực hiện tìm kiếm trên web dựa trên từ khóa trong chat và gửi kết quả cho Gemini. 🔍"""
    logger.info("Meow! Tìm kiếm được kích hoạt từ chat 🐾")

    thinking_message = f"## {EMOJI_LUNA_THINKING} Meow! Chờ một chút <@{message.author.id}>, Neko đang nghĩ... {EMOJI_BARD_THINK}"
    sent_message = await message.channel.send(content=thinking_message, reference=message)
    
    start_time = time.time()

    try:
        query = message.content  # Meow! Dùng toàn bộ tin nhắn làm truy vấn
        keywords = extract_keywords(query)  # Meow! Trích xuất từ khóa từ truy vấn

        search_results = ""
        for i in range(0, 20, 10):  # Meow! Lặp qua 2 trang kết quả (10 kết quả mỗi trang)
           result = await google_search(keywords, start=i+1)  # Meow! Tìm kiếm Google
           if result:
              search_results += result + "\n"  # Meow! Thêm vào kết quả tìm kiếm

        if search_results:
            logger.info(f"Meow! Kết quả tìm kiếm:\n {search_results}") # Meow! Ghi log kết quả
            prompt = create_search_prompt(message.channel.id, search_results, query)
            logger.debug(f"Meow! Prompt gửi đến Gemini:\n {prompt}") # Meow! Ghi log prompt
            response_text, error_message = await get_api_response(prompt)
            if response_text:
                 processing_time = round(time.time() - start_time, 2)
                 footer = await create_footer(processing_time, response_text)
                 full_response = f"{response_text}\n{footer}"
                 logger.debug(f"Meow! Phản hồi API tìm kiếm (rút gọn): {response_text[:50]}...")
                 await send_response_with_thinking(message.channel, full_response, message, sent_message)
            else:
                await sent_message.edit(content=f"Meow! Lỗi phân tích kết quả tìm kiếm: {error_message}")
        else:
            await sent_message.edit(content="Meow! Không tìm thấy kết quả hoặc có lỗi xảy ra trong quá trình tìm kiếm.")
    except Exception as e:
        log_message = f"Meow! Lỗi trong quá trình tìm kiếm: {e}"
        logger.error(log_message)
        await sent_message.edit(content="Meow! Có lỗi xảy ra trong quá trình tìm kiếm.")


# Meow! Command chat
@bot.command(name='neko', help='Meow! Chat với Neko (ví dụ: !neko bạn khỏe không?)')
async def chat(ctx, *, message: str):
    """Meow! Chat với bot trong bất kỳ channel nào. 💬"""
    thinking_message = f"## {EMOJI_LUNA_THINKING} Meow! Chờ một chút <@{ctx.author.id}>, Neko đang nghĩ... {EMOJI_BARD_THINK}"
    sent_message = await ctx.send(content=thinking_message, reference=ctx.message)

    start_time = time.time()
    
    prompt = SFW_PROMPT + f"\n\nMeow! Người dùng: {message}"
    
    key = (ctx.guild.id, ctx.author.id)
    prompt_with_context = prompt
    if key in CONTEXT_MEMORY:
        context = " ".join(CONTEXT_MEMORY[key][-CONTEXT_LIMIT*2:])
        prompt_with_context = f"{SFW_PROMPT}\n\nMeow! Bối cảnh cuộc trò chuyện trước: {context}\n\nMeow! Người dùng: {message}"
    
    response_text, error_message = await get_api_response(prompt_with_context)
    if response_text is None:
        log_message = f"Meow! Có lỗi xảy ra: {error_message}"
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
            # Meow! Thay thế code block bằng link có thể click và đuôi file
            modified_response = modified_response.replace(f"```{language_hint}\n{code}```", f"[code{extension}]({gist_url})")
        else:
             log_message = f"Meow! Có lỗi xảy ra khi tạo gist: {gist_error}"
             print(f"{datetime.now()} - ERROR - {log_message}")
             logger.error(log_message)
             modified_response = modified_response.replace(f"```{language_hint}\n{code}```", log_message)
                
    full_response = f"{modified_response}\n{footer}"
    print(f"{datetime.now()} - INFO - {full_response}")
    logger.info(full_response)
    await send_response_with_thinking(ctx.channel, full_response, ctx.message, sent_message)

@bot.event
async def on_message(message):
    """Meow! Xử lý tin nhắn đến. 🐾"""
    logger.debug(f"Meow! Nhận tin nhắn: {message.content}")
    if message.author == bot.user:
        return  # Meow! Bỏ qua tin nhắn từ bot
    asyncio.create_task(process_message(message))  # Meow! Xử lý tin nhắn còn lại như một task mới
    await bot.process_commands(message)  # Meow! Xử lý các command

@bot.event
async def on_ready():
    """Meow! Sự kiện khi bot đã sẵn sàng. 🚀"""
    log_message = f"Meow! Bot đã sẵn sàng. Đã đăng nhập với tên {bot.user}"
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)

_stop_future = None
async def stop_bot():
    """Meow! Dừng bot. 🛑"""
    log_message = "Meow! Đang dừng bot..."
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)
    if not _stop_future.done():
        _stop_future.set_result(True)
    await bot.close()
    log_message = "Meow! Bot đã dừng."
    print(f"{datetime.now()} - INFO - {log_message}")
    logger.info(log_message)

async def check_console_input(stop_future):
    """Meow! Kiểm tra input từ console để dừng bot. ⌨️"""
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
    """Meow! Hàm chính để chạy bot và kiểm tra input console. 🐾"""
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
