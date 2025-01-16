import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
from io import StringIO
from collections import defaultdict
import time

# Import the bot file
import sys
sys.path.insert(0, '.') # Add current directory to path
sys.path.insert(0, 'NekoAPI') # Add NekoAPI directory to path
import main as bot

class TestBot(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.bot = bot.bot
        self.bot.process_commands = AsyncMock() # Mock process_commands
        self.bot.start = AsyncMock()
        self.bot.close = AsyncMock()
        
        # Set environment variables for testing
        import os
        os.environ['GOOGLE_GEMINI_API_KEY'] = "test_gemini_key"
        os.environ['GOOGLE_API_KEY'] = "test_google_api_key"
        os.environ['GOOGLE_CSE_ID'] = "test_google_cse_id"
        os.environ['GITHUB_TOKEN'] = "test_github_token"
        os.environ['DISCORD_BOT_TOKEN'] = "test_discord_token"
        
        # Reset context memory before each test
        bot.CONTEXT_MEMORY = defaultdict(list)

    async def test_google_search_success(self):
        with patch('NekoAPI.main.build') as mock_build:
            mock_execute = AsyncMock(return_value={
                "items": [
                    {"title": "Test Title", "link": "test_link", "snippet": "Test Snippet"}
                ]
            })
            mock_build.return_value.cse.return_value.list.return_value.execute = mock_execute
            results = await bot.google_search("test query")
            self.assertIsInstance(results, str)
            self.assertIn("Test Title", results)
            mock_build.assert_called_once()

    async def test_google_search_no_results(self):
        with patch('NekoAPI.main.build') as mock_build:
            mock_execute = AsyncMock(return_value={})
            mock_build.return_value.cse.return_value.list.return_value.execute = mock_execute
            results = await bot.google_search("test query")
            self.assertEqual("", results)
            mock_build.assert_called_once()

    async def test_google_search_error(self):
       with patch('NekoAPI.main.build') as mock_build:
            mock_execute = AsyncMock(side_effect=Exception("API error"))
            mock_build.return_value.cse.return_value.list.return_value.execute = mock_execute
            results = await bot.google_search("test query")
            self.assertIsNone(results)
            mock_build.assert_called_once()

    def test_extract_keywords(self):
        query = "This is a test query with some keywords!"
        keywords = bot.extract_keywords(query)
        self.assertIsInstance(keywords, str)

    def test_extract_keywords_empty(self):
        query = ""
        keywords = bot.extract_keywords(query)
        self.assertEqual("", keywords)
    
    def test_extract_keywords_error(self):
        with patch('re.findall', side_effect=Exception("Regex error")):
          keywords = bot.extract_keywords("test query")
          self.assertEqual("", keywords)
    
    def test_create_search_prompt_sfw(self):
        prompt = bot.create_search_prompt(bot.ALLOWED_CHANNEL_ID, "search results", "test query")
        self.assertTrue(prompt.startswith(bot.SFW_PROMPT))
        self.assertIn("search results", prompt)
        self.assertIn("test query", prompt)

    def test_create_search_prompt_nsfw(self):
       prompt = bot.create_search_prompt(bot.NSFW_CHANNEL_ID, "search results", "test query")
       self.assertTrue(prompt.startswith(bot.NSFW_PROMPT))
       self.assertIn("search results", prompt)
       self.assertIn("test query", prompt)
    
    def test_create_search_prompt_invalid(self):
        prompt = bot.create_search_prompt(123, "search results", "test query")
        self.assertEqual("", prompt)

    @patch('NekoAPI.main.genai.GenerativeModel')
    async def test_get_api_response_success(self, mock_gen_model):
        mock_response = AsyncMock()
        mock_response.text = "Test Response"
        mock_gen_model.return_value.generate_content.return_value = mock_response
        response, error = await asyncio.wait_for(bot.get_api_response("Test Prompt"), timeout=10)
        self.assertIsInstance(response, str)
        self.assertIsNone(error)
        mock_gen_model.assert_called_once()
    
    @patch('NekoAPI.main.genai.GenerativeModel')
    async def test_get_api_response_no_text(self, mock_gen_model):
       mock_response = AsyncMock()
       mock_response.text = None
       mock_gen_model.return_value.generate_content.return_value = mock_response
       response, error = await asyncio.wait_for(bot.get_api_response("Test Prompt"), timeout=10)
       self.assertIsNone(response)
       self.assertIsInstance(error, str)
       mock_gen_model.assert_called_once()
    
    @patch('NekoAPI.main.genai.GenerativeModel')
    async def test_get_api_response_error(self, mock_gen_model):
        mock_gen_model.return_value.generate_content.side_effect = Exception("API Error")
        with self.assertRaises(Exception, msg="API Error"):
          await asyncio.wait_for(bot.get_api_response("Test Prompt"), timeout=10)
        mock_gen_model.assert_called_once()

    async def test_create_footer(self):
        footer = await bot.create_footer(1.5, "Test response")
        self.assertIn("> <a:clock:1323724990113251430> 1.5 giây", footer)
        self.assertIn("> <a:nekoears:1323728755327373465> gemini-2.0-flash-exp", footer)
        self.assertIn("> <a:CatKeyboardWarrior:1323730573390381098>", footer) #Lenient word check

    async def test_send_long_message_short(self):
        channel_mock = AsyncMock()
        await bot.send_long_message(channel_mock, "Short message\n> Footer", reference=None)
        channel_mock.send.assert_called_once()

    async def test_send_long_message_long(self):
        channel_mock = AsyncMock()
        long_text = "Sentence " * 500  # Create a long text
        await bot.send_long_message(channel_mock, f"{long_text}\n> Footer", reference=None)
        #Ensure multiple messages are sent
        self.assertGreater(channel_mock.send.call_count, 1) 
        #Ensure that the last message has a footer
        last_call_args = channel_mock.send.call_args_list[-1][1]
        self.assertIn("> Footer", last_call_args['content'])

    async def test_send_long_message_no_footer(self):
        channel_mock = AsyncMock()
        await bot.send_long_message(channel_mock, "Short message", reference=None)
        channel_mock.send.assert_called_once()
        
    async def test_send_long_message_with_file(self):
        channel_mock = AsyncMock()
        file_mock = MagicMock(spec=discord.File)
        await bot.send_long_message(channel_mock, "Short message\n> Footer", file=file_mock, reference=None)
        channel_mock.send.assert_called_once()
    
    async def test_send_response_with_thinking(self):
        channel_mock = AsyncMock()
        message_mock = AsyncMock()
        thinking_message_mock = AsyncMock()

        await bot.send_response_with_thinking(channel_mock, "Test Response", message_mock, thinking_message_mock)
        channel_mock.send.assert_called_once()
        thinking_message_mock.delete.assert_called_once()

    def test_detect_language(self):
        self.assertEqual(bot.detect_language("def test(): print('hello')"), "python")
        self.assertEqual(bot.detect_language("function test() { console.log('hello'); }"), "javascript")
        self.assertEqual(bot.detect_language("public class Test { public static void main(String[] args) { System.out.println('hello'); } }"), "java")
        self.assertEqual(bot.detect_language("#include <iostream> int main() { std::cout << 'hello'; }"), "c++")
        self.assertEqual(bot.detect_language("#include <stdio.h> int main() { printf('hello'); }"), "c")
        self.assertEqual(bot.detect_language("package main; func main(){}"), "go")
        self.assertEqual(bot.detect_language("<!DOCTYPE html><html><body><div>hello</div></body></html>"), "html")
        self.assertEqual(bot.detect_language("{ color: red; }"), "css")
        self.assertEqual(bot.detect_language("SELECT * FROM users;"), "sql")
        self.assertEqual(bot.detect_language("This is a test text."), "text")

    def test_extract_code_blocks(self):
        text = "Some text ```python\nprint('hello')\n``` more text ```javascript\nconsole.log('test')\n``` and end."
        code_blocks = bot.extract_code_blocks(text)
        self.assertEqual(len(code_blocks), 2)
        self.assertEqual(code_blocks[0], ('python', "print('hello')\n"))
        self.assertEqual(code_blocks[1], ('javascript', "console.log('test')\n"))

    def test_extract_code_blocks_no_lang(self):
        text = "Some text ```\nprint('hello')\n``` more text."
        code_blocks = bot.extract_code_blocks(text)
        self.assertEqual(len(code_blocks), 1)
        self.assertEqual(code_blocks[0], ('', "print('hello')\n"))
    
    def test_extract_code_blocks_none(self):
        text = "Some text with no code blocks"
        code_blocks = bot.extract_code_blocks(text)
        self.assertEqual(len(code_blocks), 0)

    @patch('NekoAPI.main.requests.post')
    async def test_create_and_send_gist_success(self, mock_post):
       mock_response = MagicMock()
       mock_response.raise_for_status = MagicMock()
       mock_response.json = MagicMock(return_value={"html_url": "test_gist_url"})
       mock_post.return_value = mock_response
       gist_url, extension, error = await bot.create_and_send_gist("print('hello')", "python")
       self.assertIsInstance(gist_url, str)
       self.assertEqual(extension, ".py")
       self.assertIsNone(error)
       mock_post.assert_called_once()

    @patch('NekoAPI.main.requests.post')
    async def test_create_and_send_gist_request_error(self, mock_post):
        mock_post.side_effect = bot.requests.exceptions.RequestException("Request error")
        gist_url, extension, error = await bot.create_and_send_gist("print('hello')", "python")
        self.assertIsNone(gist_url)
        self.assertIsNone(extension)
        self.assertIsInstance(error, str)

    @patch('NekoAPI.main.requests.post', side_effect=Exception("Gist Error"))
    async def test_create_and_send_gist_error(self, mock_post):
        gist_url, extension, error = await bot.create_and_send_gist("print('hello')", "python")
        self.assertIsNone(gist_url)
        self.assertIsNone(extension)
        self.assertIsInstance(error, str)
    
    async def test_process_message_ignore_bot(self):
        message_mock = AsyncMock(spec=discord.Message)
        message_mock.author = self.bot.user
        message_mock.channel.id = bot.ALLOWED_CHANNEL_ID
        thinking_message_mock = AsyncMock()
        await bot.process_message(message_mock, thinking_message_mock)
        self.bot.process_commands.assert_not_called()
        
    async def test_process_message_ignore_channel(self):
        message_mock = AsyncMock(spec=discord.Message)
        message_mock.author = AsyncMock(spec=discord.User)
        message_mock.author.id = 123
        message_mock.channel.id = 123456  #Not a valid channel
        thinking_message_mock = AsyncMock()
        await bot.process_message(message_mock, thinking_message_mock)
        self.bot.process_commands.assert_not_called()
        
    @patch('NekoAPI.main.get_api_response', return_value=("Test Response", None))
    @patch('NekoAPI.main.create_footer', return_value="Test Footer")
    @patch('NekoAPI.main.send_response_with_thinking')
    @patch('NekoAPI.main.extract_code_blocks', return_value=[])
    async def test_process_message_sfw_success(self, mock_extract_code_blocks, mock_send, mock_create_footer, mock_get_api):
        message_mock = AsyncMock(spec=discord.Message)
        message_mock.author = AsyncMock(spec=discord.User)
        message_mock.author.id = 123
        message_mock.content = "Test message"
        message_mock.channel.id = bot.ALLOWED_CHANNEL_ID
        message_mock.guild.id = 1234
        thinking_message_mock = AsyncMock()
        await bot.process_message(message_mock, thinking_message_mock)
        mock_get_api.assert_called_once()
        mock_create_footer.assert_called_once()
        mock_send.assert_called_once()
        
    @patch('NekoAPI.main.get_api_response', return_value=("Test Response", None))
    @patch('NekoAPI.main.create_footer', return_value="Test Footer")
    @patch('NekoAPI.main.send_response_with_thinking')
    @patch('NekoAPI.main.extract_code_blocks', return_value=[])
    async def test_process_message_nsfw_success(self, mock_extract_code_blocks, mock_send, mock_create_footer, mock_get_api):
        message_mock = AsyncMock(spec=discord.Message)
        message_mock.author = AsyncMock(spec=discord.User)
        message_mock.author.id = 123
        message_mock.content = "Test message"
        message_mock.channel.id = bot.NSFW_CHANNEL_ID
        message_mock.guild.id = 1234
        thinking_message_mock = AsyncMock()
        await bot.process_message(message_mock, thinking_message_mock)
        mock_get_api.assert_called_once()
        mock_create_footer.assert_called_once()
        mock_send.assert_called_once()

    @patch('NekoAPI.main.get_api_response', return_value=(None, "API Error"))
    async def test_process_message_api_error(self, mock_get_api):
        message_mock = AsyncMock(spec=discord.Message)
        message_mock.author = AsyncMock(spec=discord.User)
        message_mock.author.id = 123
        message_mock.content = "Test message"
        message_mock.channel.id = bot.ALLOWED_CHANNEL_ID
        thinking_message_mock = AsyncMock()
        await bot.process_message(message_mock, thinking_message_mock)
        mock_get_api.assert_called_once()
        message_mock.channel.send.assert_called_once()
    
    @patch('NekoAPI.main.get_api_response', return_value=("Test Response with ```python\ncode```", None))
    @patch('NekoAPI.main.create_footer', return_value="Test Footer")
    @patch('NekoAPI.main.send_response_with_thinking')
    @patch('NekoAPI.main.create_and_send_gist', return_value=("test_gist_url",".py", None))
    async def test_process_message_code_block(self, mock_gist, mock_send, mock_create_footer, mock_get_api):
       message_mock = AsyncMock(spec=discord.Message)
       message_mock.author = AsyncMock(spec=discord.User)
       message_mock.author.id = 123
       message_mock.content = "Test message"
       message_mock.channel.id = bot.ALLOWED_CHANNEL_ID
       message_mock.guild.id = 1234
       thinking_message_mock = AsyncMock()
       await bot.process_message(message_mock, thinking_message_mock)
       mock_get_api.assert_called_once()
       mock_create_footer.assert_called_once()
       mock_send.assert_called_once()
       mock_gist.assert_called_once()

    @patch('NekoAPI.main.get_api_response', return_value=("Test Response", None))
    @patch('NekoAPI.main.create_footer', return_value="Test Footer")
    @patch('NekoAPI.main.send_response_with_thinking')
    @patch('NekoAPI.main.extract_code_blocks', return_value=[])
    async def test_process_message_context(self, mock_extract_code_blocks, mock_send, mock_create_footer, mock_get_api):
       message_mock = AsyncMock(spec=discord.Message)
       message_mock.author = AsyncMock(spec=discord.User)
       message_mock.author.id = 123
       message_mock.content = "Test message"
       message_mock.channel.id = bot.ALLOWED_CHANNEL_ID
       message_mock.guild.id = 1234
       thinking_message_mock = AsyncMock()
       
       await bot.process_message(message_mock, thinking_message_mock)
       await bot.process_message(message_mock, thinking_message_mock) # Call again to test context
       
       self.assertEqual(mock_get_api.call_count, 2) # Should be called twice, first for the message and next for the context
       mock_create_footer.assert_called()
       mock_send.assert_called()
    
    @patch('NekoAPI.main.extract_keywords', return_value="test query")
    @patch('NekoAPI.main.google_search', return_value="search results")
    @patch('NekoAPI.main.create_search_prompt', return_value="test prompt")
    @patch('NekoAPI.main.get_api_response', return_value=("Test Response", None))
    @patch('NekoAPI.main.send_response_with_thinking')
    async def test_search_command_success(self, mock_send, mock_api, mock_prompt, mock_search, mock_keywords):
        ctx_mock = AsyncMock(spec=commands.Context)
        ctx_mock.channel.id = bot.ALLOWED_CHANNEL_ID
        ctx_mock.message.author.id = 123
        await bot.search(ctx_mock, query="test query")
        mock_search.assert_called_once()
        mock_prompt.assert_called_once()
        mock_api.assert_called_once()
        mock_send.assert_called_once()
        
    @patch('NekoAPI.main.extract_keywords', return_value="test query")
    @patch('NekoAPI.main.google_search', return_value=None)
    async def test_search_command_no_search_results(self, mock_search, mock_keywords):
        ctx_mock = AsyncMock(spec=commands.Context)
        ctx_mock.channel.id = bot.ALLOWED_CHANNEL_ID
        await bot.search(ctx_mock, query="test query")
        ctx_mock.send.assert_called_once_with("No results found or an error occurred during the search.")
        mock_search.assert_called_once()

    @patch('NekoAPI.main.extract_keywords', return_value="test query")
    @patch('NekoAPI.main.google_search', side_effect=Exception("Search Error"))
    async def test_search_command_error(self, mock_search, mock_keywords):
        ctx_mock = AsyncMock(spec=commands.Context)
        ctx_mock.channel.id = bot.ALLOWED_CHANNEL_ID
        await bot.search(ctx_mock, query="test query")
        ctx_mock.send.assert_called_once_with("An error occurred during the search.")
        mock_search.assert_called_once()
    
    @patch('NekoAPI.main.process_message')
    @patch('NekoAPI.main.send_long_message')
    async def test_on_message(self, mock_send_long, mock_process_message):
       message_mock = AsyncMock(spec=discord.Message)
       message_mock.author = AsyncMock(spec=discord.User)
       message_mock.author.id = 123
       message_mock.content = "Test Message"
       message_mock.channel.send = AsyncMock() # Mock channel send
       await bot.on_message(message_mock)
       mock_process_message.assert_called_once()
       self.bot.process_commands.assert_called_once()
    
    @patch('NekoAPI.main.process_message')
    async def test_on_message_bot_ignore(self, mock_process_message):
        message_mock = AsyncMock(spec=discord.Message)
        message_mock.author = self.bot.user
        await bot.on_message(message_mock)
        mock_process_message.assert_not_called()
        self.bot.process_commands.assert_not_called()

    async def test_on_ready(self):
        with patch('sys.stdout', new_callable=StringIO) as stdout_mock:
            await bot.on_ready()
            self.assertIn("Bot is ready", stdout_mock.getvalue())
    
    @patch('NekoAPI.main.stop_bot')
    @patch('asyncio.get_running_loop')
    async def test_check_console_input_stop(self, mock_loop, mock_stop_bot):
        mock_future = asyncio.Future()
        mock_executor = MagicMock()
        mock_executor.run_in_executor.return_value = "stop"
        mock_loop.return_value.run_in_executor = mock_executor
        await bot.check_console_input(mock_future)
        mock_stop_bot.assert_called_once()

    @patch('asyncio.get_running_loop')
    async def test_check_console_input_eof(self, mock_loop):
       mock_future = asyncio.Future()
       mock_executor = MagicMock()
       mock_executor.run_in_executor = AsyncMock(side_effect=EOFError()) # Change here so that an awaitable mock object is used
       mock_loop.return_value.run_in_executor = mock_executor
       await bot.check_console_input(mock_future)
    
    @patch('NekoAPI.main.stop_bot')
    @patch('NekoAPI.main.check_console_input')
    async def test_main_keyboard_interrupt(self, mock_check_input, mock_stop_bot):
        self.bot.start.side_effect = KeyboardInterrupt
        await bot.main()
        mock_stop_bot.assert_called_once()
    
    @patch('NekoAPI.main.stop_bot')
    @patch('NekoAPI.main.check_console_input')
    async def test_main_bot_start_error(self, mock_check_input, mock_stop_bot):
        self.bot.start.side_effect = Exception
        await bot.main()
        mock_stop_bot.assert_called_once()

    @patch('NekoAPI.main.stop_bot')
    @patch('NekoAPI.main.check_console_input')
    async def test_main_success(self, mock_check_input, mock_stop_bot):
        mock_check_input.return_value = None
        await bot.main()
        self.bot.start.assert_called_once()

if __name__ == '__main__':
    unittest.main()
