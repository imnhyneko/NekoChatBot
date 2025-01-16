import unittest
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
import os
import asyncio
import json
from collections import defaultdict
from datetime import datetime
from io import StringIO  # Import StringIO
import sys  # Import sys

# Get the absolute path to the NekoAPI directory
NekoAPI_PATH = os.path.join(os.environ.get("GITHUB_WORKSPACE", ""), "NekoAPI")
sys.path.append(NekoAPI_PATH)

# Import các hàm và biến từ bot.py nằm trong thư mục NekoAPI
from bot import process_message, get_api_response, google_search, extract_keywords, create_search_prompt, create_footer, send_long_message, detect_language, extract_code_blocks, create_and_send_gist, main, stop_bot
from bot import CONTEXT_MEMORY, CONTEXT_LIMIT, SFW_PROMPT, NSFW_PROMPT, ALLOWED_CHANNEL_ID, NSFW_CHANNEL_ID, bot, logger, log_filepath

# Load the test environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__),'.env.test'))

class TestBot(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.mock_message = AsyncMock()
        self.mock_message.author.id = 12345
        self.mock_message.guild.id = 67890
        self.mock_message.channel.id = ALLOWED_CHANNEL_ID
        self.mock_message.content = "Test message"
        self.mock_message.channel.send = AsyncMock()
        self.mock_message.reference = None
        self.mock_message.reply = AsyncMock()
        self.mock_message.channel.create_thread = AsyncMock(return_value=AsyncMock(id=112233))
        self.mock_message.author.bot = False
        self.mock_thinking_message = AsyncMock()
        self.mock_thinking_message.delete = AsyncMock()
        self.mock_thinking_message.edit = AsyncMock()
        self.mock_thinking_message.reference = self.mock_message
        
    # Test Case 1: Test for message processing logic
    @patch('bot.get_api_response')
    async def test_process_message_sfw(self, mock_get_api_response):
        mock_get_api_response.return_value = ("Test response", None)
        
        await process_message(self.mock_message, self.mock_thinking_message)
        self.mock_message.channel.send.assert_called()
        sent_content = self.mock_message.channel.send.call_args[1]["content"]
        self.assertIn("Test response", sent_content)

    @patch('bot.get_api_response')
    async def test_process_message_nsfw(self, mock_get_api_response):
        mock_get_api_response.return_value = ("Test NSFW response", None)
        self.mock_message.channel.id = NSFW_CHANNEL_ID
        
        await process_message(self.mock_message, self.mock_thinking_message)
        self.mock_message.channel.send.assert_called()
        sent_content = self.mock_message.channel.send.call_args[1]["content"]
        self.assertIn("Test NSFW response", sent_content)

    @patch('bot.get_api_response')
    async def test_process_message_not_allowed(self, mock_get_api_response):
        mock_get_api_response.return_value = ("Test response", None)
        self.mock_message.channel.id = 9999
        
        await process_message(self.mock_message, self.mock_thinking_message)
        self.mock_message.channel.send.assert_not_called()
        mock_get_api_response.assert_not_called()

    # Test Case 2: Test for API Response
    @patch('bot.genai.GenerativeModel')
    async def test_get_api_response_success(self, mock_gen_model):
        mock_response = MagicMock()
        mock_response.text = "Test API response"
        mock_gen_model_instance = MagicMock()
        mock_gen_model_instance.generate_content.return_value = mock_response
        mock_gen_model.return_value = mock_gen_model_instance

        response, error = await get_api_response("Test prompt")
        self.assertEqual(response, "Test API response")
        self.assertIsNone(error)

    @patch('bot.genai.GenerativeModel')
    async def test_get_api_response_no_text(self, mock_gen_model):
         mock_response = MagicMock()
         mock_response.text = None
         mock_gen_model_instance = MagicMock()
         mock_gen_model_instance.generate_content.return_value = mock_response
         mock_gen_model.return_value = mock_gen_model_instance
        
         response, error = await get_api_response("Test prompt")
         self.assertIsNone(response)
         self.assertIn("No text content found in the response.", error)

    @patch('bot.genai.GenerativeModel')
    async def test_get_api_response_error(self, mock_gen_model):
        mock_gen_model_instance = MagicMock()
        mock_gen_model_instance.generate_content.side_effect = Exception("API error")
        mock_gen_model.return_value = mock_gen_model_instance

        with self.assertRaises(Exception):
            await get_api_response("Test prompt")
            
    # Test Case 3: Test for Google Search
    @patch('bot.build')
    async def test_google_search_success(self, mock_build):
       mock_service = MagicMock()
       mock_list_call = MagicMock()
       mock_execute = MagicMock()
       
       mock_execute.return_value = {
           'items': [
               {'title': 'Test Title 1', 'link': 'https://example.com/1', 'snippet': 'Test snippet 1'},
               {'title': 'Test Title 2', 'link': 'https://example.com/2', 'snippet': 'Test snippet 2'}
           ]
       }
       mock_list_call.execute = mock_execute
       mock_service.cse.return_value.list = mock_list_call
       mock_build.return_value = mock_service
       
       results = await google_search("test query")
       self.assertIn("- [Test Title 1](https://example.com/1)", results)
       self.assertIn("Test snippet 1", results)
       self.assertIn("- [Test Title 2](https://example.com/2)", results)
       self.assertIn("Test snippet 2", results)
    
    @patch('bot.build')
    async def test_google_search_no_results(self, mock_build):
        mock_service = MagicMock()
        mock_list_call = MagicMock()
        mock_execute = MagicMock()
        
        mock_execute.return_value = {}  # No items
        mock_list_call.execute = mock_execute
        mock_service.cse.return_value.list = mock_list_call
        mock_build.return_value = mock_service
        
        results = await google_search("test query")
        self.assertEqual(results, "")
    
    @patch('bot.build')
    async def test_google_search_error(self, mock_build):
       mock_service = MagicMock()
       mock_list_call = MagicMock()
       mock_execute = MagicMock()
       
       mock_execute.side_effect = Exception("API error")
       mock_list_call.execute = mock_execute
       mock_service.cse.return_value.list = mock_list_call
       mock_build.return_value = mock_service
       
       results = await google_search("test query")
       self.assertIsNone(results)


    # Test Case 4: Test for Keyword Extraction
    def test_extract_keywords_success(self):
        query = "This is a Test query with Some Keywords"
        expected_keywords = "this is a test query with some keywords"
        self.assertEqual(extract_keywords(query), expected_keywords)

    def test_extract_keywords_empty(self):
        query = ""
        expected_keywords = ""
        self.assertEqual(extract_keywords(query), expected_keywords)

    def test_extract_keywords_with_special_characters(self):
         query = "!@#$%^ Test query"
         expected_keywords = "test query"
         self.assertEqual(extract_keywords(query), expected_keywords)
    
    # Test Case 5: Test for Search Prompt creation
    def test_create_search_prompt_sfw(self):
        search_results = "Test Search Results"
        query = "Test Query"
        expected_prompt = f"{SFW_PROMPT}\n\nDựa vào thông tin sau đây để trả lời câu hỏi: {query}\n\nThông tin tìm kiếm:\n{search_results}"
        self.assertEqual(create_search_prompt(ALLOWED_CHANNEL_ID, search_results, query), expected_prompt)

    def test_create_search_prompt_nsfw(self):
        search_results = "Test NSFW Search Results"
        query = "Test NSFW Query"
        expected_prompt = f"{NSFW_PROMPT}\n\nDựa vào thông tin sau đây để trả lời câu hỏi: {query}\n\nThông tin tìm kiếm:\n{search_results}"
        self.assertEqual(create_search_prompt(NSFW_CHANNEL_ID, search_results, query), expected_prompt)

    def test_create_search_prompt_not_allowed(self):
        search_results = "Test Results"
        query = "Test Query"
        expected_prompt = ""
        self.assertEqual(create_search_prompt(9999, search_results, query), expected_prompt)

    # Test Case 6: Test for Footer creation
    async def test_create_footer(self):
        processing_time = 1.23
        text_response = "This is a test response."
        expected_footer = (f"> <a:clock:1323724990113251430> {processing_time} giây\n"
              f"> <a:nekoears:1323728755327373465> gemini-2.0-flash-exp\n"
              f"> <a:CatKeyboardWarrior:1323730573390381098> {len(text_response.split())} từ\n")
        self.assertEqual(await create_footer(processing_time, text_response), expected_footer)

    # Test Case 7: Test for Send long message
    @patch('bot.discord.TextChannel')
    async def test_send_long_message_short(self, MockTextChannel):
        mock_channel = MockTextChannel()
        mock_channel.send = AsyncMock() #Use AsyncMock for send method
        test_content = "Short content"
        test_footer = "> Footer"
        await send_long_message(mock_channel, f"{test_content}\n{test_footer}")
        mock_channel.send.assert_called_with(content=f"{test_content}\n{test_footer}", file=None, reference=None)

    @patch('bot.discord.TextChannel')
    async def test_send_long_message_long(self, MockTextChannel):
        mock_channel = MockTextChannel()
        mock_channel.send = AsyncMock() #Use AsyncMock for send method
        long_content = "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5. " * 300
        test_footer = "> Footer"
        await send_long_message(mock_channel, f"{long_content}\n{test_footer}")
        
        call_args_list = mock_channel.send.call_args_list
        self.assertTrue(len(call_args_list) > 1)
        
        last_call = call_args_list[-1][1]["content"]
        self.assertIn(test_footer, last_call)
    
    @patch('bot.discord.TextChannel')
    async def test_send_long_message_long_no_sentence(self, MockTextChannel):
         mock_channel = MockTextChannel()
         mock_channel.send = AsyncMock() #Use AsyncMock for send method
         long_content = "a" * 3000
         test_footer = "> Footer"
         await send_long_message(mock_channel, f"{long_content}\n{test_footer}")
        
         call_args_list = mock_channel.send.call_args_list
         self.assertTrue(len(call_args_list) > 1)
         
         last_call = call_args_list[-1][1]["content"]
         self.assertIn(test_footer, last_call)

    @patch('bot.discord.TextChannel')
    async def test_send_long_message_with_file(self, MockTextChannel):
        mock_channel = MockTextChannel()
        mock_channel.send = AsyncMock() #Use AsyncMock for send method
        content = "Test content with file"
        mock_file = AsyncMock()
        
        await send_long_message(mock_channel, content, file=mock_file)
        
        mock_channel.send.assert_called_once_with(content=content, file=mock_file, reference=None)

    # Test Case 8: Test Language Detection
    def test_detect_language_python(self):
        code = "def my_function():\n  print('Hello')\nimport os"
        self.assertEqual(detect_language(code), "python")

    def test_detect_language_javascript(self):
        code = "function my_function() {\n  console.log('Hello');\n let x = 10; }"
        self.assertEqual(detect_language(code), "javascript")
    
    def test_detect_language_java(self):
       code = "public class Main {\n  public static void main(String[] args) {\n  System.out.println('Hello')}}\n"
       self.assertEqual(detect_language(code), "java")
    
    def test_detect_language_cplusplus(self):
       code = "#include <iostream>\nint main() {\n std::cout << 'Hello'; \n}"
       self.assertEqual(detect_language(code), "c++")

    def test_detect_language_c(self):
        code = "#include <stdio.h>\nint main() {\n printf('Hello'); \n}"
        self.assertEqual(detect_language(code), "c")

    def test_detect_language_go(self):
         code = "package main\nfunc main() {\n println('Hello')\n}"
         self.assertEqual(detect_language(code), "go")

    def test_detect_language_html(self):
       code = "<!DOCTYPE html>\n<html>\n<body>\n<div>Test</div></body></html>"
       self.assertEqual(detect_language(code), "html")
    
    def test_detect_language_css(self):
        code = "body {\n color: red; \n background: white;} "
        self.assertEqual(detect_language(code), "css")

    def test_detect_language_sql(self):
      code = "select * from users where id = 1"
      self.assertEqual(detect_language(code), "sql")

    def test_detect_language_text(self):
        code = "This is just a text."
        self.assertEqual(detect_language(code), "text")

    # Test Case 9: Test Code Block Extraction
    def test_extract_code_blocks_with_language(self):
        text = "This is text. ```python\nprint('Hello')\n``` More text. ```javascript\nconsole.log('World')\n```"
        expected_blocks = [('python', "print('Hello')\n"), ('javascript', "console.log('World')\n")]
        self.assertEqual(extract_code_blocks(text), expected_blocks)

    def test_extract_code_blocks_no_language(self):
        text = "This is text. ```\nprint('Hello')\n``` More text. ```\nconsole.log('World')\n```"
        expected_blocks = [('', "print('Hello')\n"), ('', "console.log('World')\n")]
        self.assertEqual(extract_code_blocks(text), expected_blocks)

    def test_extract_code_blocks_no_code(self):
         text = "This is a test without code."
         self.assertEqual(extract_code_blocks(text), [])
    
    # Test Case 10: Test Gist creation and response
    @patch('bot.requests.post')
    async def test_create_and_send_gist_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {'html_url': 'https://gist.github.com/test_gist'}
        mock_post.return_value = mock_response
        
        url, extension, error = await create_and_send_gist("test code", "python")
        self.assertEqual(url, "https://gist.github.com/test_gist")
        self.assertEqual(extension, ".py")
        self.assertIsNone(error)

    @patch('bot.requests.post')
    async def test_create_and_send_gist_request_error(self, mock_post):
        mock_post.side_effect = Exception("Request Error")

        url, extension, error = await create_and_send_gist("test code", "python")
        self.assertIsNone(url)
        self.assertIsNone(extension)
        self.assertIn("Request Error", error)

    @patch('bot.requests.post')
    async def test_create_and_send_gist_api_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response

        url, extension, error = await create_and_send_gist("test code", "python")
        self.assertIsNone(url)
        self.assertIsNone(extension)
        self.assertIn("API Error", error)

    @patch('bot.requests.post')
    async def test_create_and_send_gist_no_url(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        url, extension, error = await create_and_send_gist("test code", "python")
        self.assertIsNone(url)
        self.assertIsNone(extension)
        self.assertIsNone(error)
    
    # Test Case 11: Test Context Memory
    @patch('bot.get_api_response')
    async def test_context_memory_usage(self, mock_get_api_response):
        mock_get_api_response.return_value = ("Test response", None)
        
        key = (self.mock_message.guild.id, self.mock_message.author.id)
        
        await process_message(self.mock_message, self.mock_thinking_message)
        self.assertTrue(key in CONTEXT_MEMORY)
        self.assertEqual(len(CONTEXT_MEMORY[key]), 2)
        
        self.mock_message.content = "Second test message"
        await process_message(self.mock_message, self.mock_thinking_message)
        self.assertEqual(len(CONTEXT_MEMORY[key]), 4)
        
        # Check if old context is sent to Gemini.
        mock_get_api_response.return_value = ("New response", None)
        await process_message(self.mock_message, self.mock_thinking_message)
        prompt_sent = mock_get_api_response.call_args[0][0]
        self.assertIn("Bối cảnh cuộc trò chuyện trước: Test message Test response Second test message New response", prompt_sent)

    @patch('bot.get_api_response')
    async def test_context_memory_limit(self, mock_get_api_response):
        mock_get_api_response.return_value = ("Test response", None)
        
        key = (self.mock_message.guild.id, self.mock_message.author.id)

        for i in range(CONTEXT_LIMIT + 5):
            self.mock_message.content = f"Test message {i}"
            await process_message(self.mock_message, self.mock_thinking_message)
            
        self.assertTrue(len(CONTEXT_MEMORY[key]) <= CONTEXT_LIMIT * 2)
        # Check if oldest context is not sent to Gemini.
        prompt_sent = mock_get_api_response.call_args[0][0]
        self.assertNotIn(f"Test message 0", prompt_sent)

    @patch('bot.get_api_response')
    async def test_context_memory_different_user(self, mock_get_api_response):
         mock_get_api_response.return_value = ("Test response", None)
         
         key1 = (self.mock_message.guild.id, self.mock_message.author.id)
         await process_message(self.mock_message, self.mock_thinking_message)

         self.mock_message.author.id = 54321
         key2 = (self.mock_message.guild.id, self.mock_message.author.id)
         await process_message(self.mock_message, self.mock_thinking_message)
         
         self.assertTrue(key1 in CONTEXT_MEMORY)
         self.assertTrue(key2 in CONTEXT_MEMORY)
         self.assertNotEqual(CONTEXT_MEMORY[key1], CONTEXT_MEMORY[key2])

    @patch('bot.get_api_response')
    async def test_context_memory_different_guild(self, mock_get_api_response):
         mock_get_api_response.return_value = ("Test response", None)
         
         key1 = (self.mock_message.guild.id, self.mock_message.author.id)
         await process_message(self.mock_message, self.mock_thinking_message)

         self.mock_message.guild.id = 54321
         key2 = (self.mock_message.guild.id, self.mock_message.author.id)
         await process_message(self.mock_message, self.mock_thinking_message)
         
         self.assertTrue(key1 in CONTEXT_MEMORY)
         self.assertTrue(key2 in CONTEXT_MEMORY)
         self.assertNotEqual(CONTEXT_MEMORY[key1], CONTEXT_MEMORY[key2])
    
    # Test case 12: Test for search command
    @patch('bot.google_search')
    @patch('bot.get_api_response')
    async def test_search_command_success(self, mock_get_api_response, mock_google_search):
        mock_google_search.return_value = "Test Search Results"
        mock_get_api_response.return_value = ("Test response", None)
        
        mock_ctx = AsyncMock()
        mock_ctx.message.author.id = 12345
        mock_ctx.message.author.bot = False
        mock_ctx.channel.id = ALLOWED_CHANNEL_ID
        mock_ctx.send = AsyncMock()
        mock_ctx.message = self.mock_message
        
        await bot.get_command("timkiem").callback(mock_ctx, query="test query")
        mock_ctx.send.assert_called()
        sent_content = mock_ctx.send.call_args[1]["content"]
        self.assertIn("Test response", sent_content)

    @patch('bot.google_search')
    async def test_search_command_no_results(self, mock_google_search):
        mock_google_search.return_value = None

        mock_ctx = AsyncMock()
        mock_ctx.message.author.id = 12345
        mock_ctx.message.author.bot = False
        mock_ctx.channel.id = ALLOWED_CHANNEL_ID
        mock_ctx.send = AsyncMock()
        mock_ctx.message = self.mock_message

        await bot.get_command("timkiem").callback(mock_ctx, query="test query")
        mock_ctx.send.assert_called_with("No results found or an error occurred during the search.")

    @patch('bot.google_search')
    @patch('bot.get_api_response')
    async def test_search_command_error(self, mock_get_api_response, mock_google_search):
         mock_google_search.return_value = "Test Search Results"
         mock_get_api_response.return_value = (None, "Error analyzing search results.")
        
         mock_ctx = AsyncMock()
         mock_ctx.message.author.id = 12345
         mock_ctx.message.author.bot = False
         mock_ctx.channel.id = ALLOWED_CHANNEL_ID
         mock_ctx.send = AsyncMock()
         mock_ctx.message = self.mock_message

         await bot.get_command("timkiem").callback(mock_ctx, query="test query")
         mock_ctx.send.assert_called()
         sent_content = mock_ctx.send.call_args[0]
         self.assertIn("Error analyzing search results.", sent_content)

    @patch('bot.google_search')
    async def test_search_command_search_error(self, mock_google_search):
        mock_google_search.side_effect = Exception("Search Error")
        
        mock_ctx = AsyncMock()
        mock_ctx.message.author.id = 12345
        mock_ctx.message.author.bot = False
        mock_ctx.channel.id = ALLOWED_CHANNEL_ID
        mock_ctx.send = AsyncMock()
        mock_ctx.message = self.mock_message

        await bot.get_command("timkiem").callback(mock_ctx, query="test query")
        mock_ctx.send.assert_called_with("An error occurred during the search.")

    # Test Case 13: Test on_message and command process
    @patch('bot.process_message')
    async def test_on_message(self, mock_process_message):
        mock_message = AsyncMock()
        mock_message.author.id = 12345
        mock_message.guild.id = 67890
        mock_message.channel.id = ALLOWED_CHANNEL_ID
        mock_message.content = "Test message"
        mock_message.author = AsyncMock()
        mock_message.author.bot = False
        mock_message.channel.send = AsyncMock()
        mock_message.channel.id = 12345 # Mock ID of message.channel
        
        # Use the real bot object to process commands
        await bot.on_message(mock_message)
        mock_process_message.assert_called()
        await mock_message.channel.send.assert_called()

    @patch('bot.process_message')
    async def test_on_message_bot_user(self, mock_process_message):
         mock_message = AsyncMock()
         mock_message.author = bot.user
         mock_message.channel.send = AsyncMock()

         await bot.on_message(mock_message)
         mock_process_message.assert_not_called()
         mock_message.channel.send.assert_not_called()
    
    # Test Case 14: Test stop bot
    @patch('asyncio.Future')
    async def test_stop_bot(self, MockFuture):
       future = MockFuture()
       future.done.return_value = False
       bot._stop_future = future
       bot.close = AsyncMock()
       await stop_bot()
       self.assertTrue(future.set_result.called)
       self.assertTrue(bot.close.called)
       

    @patch('asyncio.Future')
    async def test_stop_bot_already_done(self, MockFuture):
        future = MockFuture()
        future.done.return_value = True
        bot._stop_future = future
        bot.close = AsyncMock()
        await stop_bot()
        self.assertFalse(future.set_result.called)
        self.assertTrue(bot.close.called)
    
    # Test Case 16: Test main and close
    @patch('bot.bot.start')
    @patch('bot.check_console_input')
    async def test_main_normal_close(self, mock_check_console_input, mock_bot_start):
        mock_bot_start.side_effect = asyncio.CancelledError
        mock_check_console_input.return_value = None
        
        with self.assertRaises(asyncio.CancelledError):
            await main()
        
        # Additional check to see if bot.start was called once
        mock_bot_start.assert_called_once()

    @patch('bot.bot.start')
    @patch('bot.check_console_input')
    async def test_main_keyboard_interrupt(self, mock_check_console_input, mock_bot_start):
        mock_bot_start.side_effect = KeyboardInterrupt
        mock_check_console_input.return_value = None
        bot.close = AsyncMock()

        await main()
        
        # Check that bot.start was called
        mock_bot_start.assert_called_once()
        self.assertTrue(bot.close.called)
    
    @patch('bot.bot.start')
    @patch('bot.check_console_input')
    async def test_main_no_interrupt(self, mock_check_console_input, mock_bot_start):
       
        async def _mock_check_console_input(stop_future):
            await asyncio.sleep(0.1) # Simulate waiting for user input
            stop_future.set_result(True)
            return
        
        mock_check_console_input.side_effect = _mock_check_console_input
        mock_bot_start.side_effect = asyncio.CancelledError # make it close normally
        
        with self.assertRaises(asyncio.CancelledError):
           await main()
        
        # Check that bot.start was called once
        mock_bot_start.assert_called_once()

if __name__ == '__main__':
    unittest.main()
