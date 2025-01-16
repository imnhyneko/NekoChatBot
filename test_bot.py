import unittest
import asyncio
from unittest.mock import MagicMock, patch
from io import StringIO
import os
import datetime
import logging
import re
import sys
import json
import textwrap
from collections import defaultdict

# Import your bot script
from bot import (
    bot,
    get_api_response,
    create_footer,
    send_long_message,
    detect_language,
    extract_code_blocks,
    create_and_send_gist,
    process_message,
    SFW_PROMPT,
    NSFW_PROMPT,
    ALLOWED_CHANNEL_ID,
    NSFW_CHANNEL_ID,
    CONTEXT_MEMORY,
    CONTEXT_LIMIT,
    extract_keywords,
    google_search,
    create_search_prompt,
    _stop_future,
    stop_bot
    send_response_with_thinking
)

# Load environment variables for testing
from dotenv import load_dotenv
load_dotenv()

class TestBot(unittest.TestCase):
     def setUp(self):
        # Clear context memory before each test
         CONTEXT_MEMORY.clear()
         self.log_capture_string = StringIO()
         logging.getLogger().addHandler(logging.StreamHandler(self.log_capture_string))
         logging.getLogger().setLevel(logging.DEBUG) # Set logging to debug during testing

     def tearDown(self):
         self.log_capture_string.close() # Close the buffer after each test
         # Clean up log handlers, particularly file handler, at the end of each test, to ensure it is not retained between test runs
         log = logging.getLogger()
         log.handlers = [
                h for h in log.handlers
                if not isinstance(h, logging.FileHandler)
          ]
     
     def get_log_messages(self):
         """Helper to get all logged messages"""
         return self.log_capture_string.getvalue()
     
     def assert_log_contains(self, expected_text, level=logging.DEBUG):
        """Helper function to assert log content."""
        log_messages = self.get_log_messages()
        expected_log_pattern = re.compile(re.escape(expected_text))
        match = expected_log_pattern.search(log_messages)
        self.assertIsNotNone(match, f"Expected log message '{expected_text}' not found in logs at level {level} \n {log_messages}")
     
     def assert_log_not_contains(self, unexpected_text, level=logging.DEBUG):
        """Helper function to assert log absence."""
        log_messages = self.get_log_messages()
        expected_log_pattern = re.compile(re.escape(unexpected_text))
        match = expected_log_pattern.search(log_messages)
        self.assertIsNone(match, f"Unexpected log message '{unexpected_text}' found in logs at level {level} \n {log_messages}")
     
     def assert_contains_footer(self, content, processing_time):
          footer = (f"> <a:clock:1323724990113251430> {processing_time} giây\n"
                f"> <a:nekoears:1323728755327373465> gemini-2.0-flash-exp\n"
                f"> <a:CatKeyboardWarrior:1323730573390381098> \d+ từ\n") #Regex for word counts
          match = re.search(footer, content)
          self.assertIsNotNone(match, f"Footer with expected time '{processing_time}' not found in content. \n {content}")
     
     @patch('main.genai.GenerativeModel')
     async def test_get_api_response(self, mock_genai_model):
         mock_response = MagicMock()
         mock_response.text = "Test API Response"
         mock_genai_model.return_value.generate_content.return_value = mock_response
         
         prompt = "Test Prompt"
         response, error = await get_api_response(prompt)
         
         self.assertEqual(response, "Test API Response")
         self.assertIsNone(error)
         
         mock_genai_model.assert_called_once()
         mock_genai_model.return_value.generate_content.assert_called_once_with(prompt)
         self.assert_log_contains("API Response (truncated): Test API Response...")
     
     @patch('main.genai.GenerativeModel')
     async def test_get_api_response_no_text(self, mock_genai_model):
        mock_response = MagicMock()
        mock_response.text = None
        mock_genai_model.return_value.generate_content.return_value = mock_response
        
        prompt = "Test Prompt"
        response, error = await get_api_response(prompt)
        
        self.assertIsNone(response)
        self.assertEqual(error, "No text content found in the response.")
        self.assert_log_contains("Full API Response (no text):")
     
     async def test_create_footer(self):
         processing_time = 1.23
         text_response = "This is a test response."
         footer = await create_footer(processing_time, text_response)
         self.assert_contains_footer(footer, processing_time)
     
     @patch("main.send_long_message")
     async def test_send_response_with_thinking(self, mock_send_long_message):
          mock_channel = MagicMock()
          mock_message = MagicMock()
          mock_thinking_message = MagicMock()
          mock_thinking_message.delete = MagicMock()
          
          response_text = "Test Response"
          await send_response_with_thinking(mock_channel, response_text, mock_message, mock_thinking_message)

          mock_send_long_message.assert_called_once_with(mock_channel, response_text, reference=mock_message)
          mock_thinking_message.delete.assert_called_once()
    
     @patch('main.requests.post')
     async def test_create_and_send_gist(self, mock_post):
          mock_response = MagicMock()
          mock_response.raise_for_status = MagicMock()
          mock_response.json = MagicMock(return_value={"html_url": "https://gist.github.com/test_url"})
          mock_post.return_value = mock_response

          code = "print('hello')"
          language = "python"
          gist_url, extension, error = await create_and_send_gist(code, language)
          
          self.assertEqual(gist_url, "https://gist.github.com/test_url")
          self.assertEqual(extension, ".py")
          self.assertIsNone(error)
          
          mock_post.assert_called_once()
     
     @patch('main.requests.post')
     async def test_create_and_send_gist_error(self, mock_post):
        mock_post.side_effect = Exception("Test Error")
        code = "print('hello')"
        language = "python"
        gist_url, extension, error = await create_and_send_gist(code, language)
        self.assertIsNone(gist_url)
        self.assertIsNone(extension)
        self.assertIsNotNone(error)
        self.assert_log_contains("Gist Error: Test Error")
     
     def test_detect_language(self):
          self.assertEqual(detect_language("def hello(): print('test')"), "python")
          self.assertEqual(detect_language("function test(){}"), "javascript")
          self.assertEqual(detect_language("public class Test {}"), "java")
          self.assertEqual(detect_language("#include <iostream>"), "c++")
          self.assertEqual(detect_language("#include <stdio.h>"), "c")
          self.assertEqual(detect_language("package main; func main() {}"), "go")
          self.assertEqual(detect_language("<!DOCTYPE html>"), "html")
          self.assertEqual(detect_language("body { color: blue; }"), "css")
          self.assertEqual(detect_language("select * from users;"), "sql")
          self.assertEqual(detect_language("This is just regular text"), "text")
     
     def test_extract_code_blocks(self):
        text = "This is some text `code1` and ```python\n code2 \n``` more text ```javascript code3```"
        code_blocks = extract_code_blocks(text)
        self.assertEqual(len(code_blocks), 2)
        self.assertEqual(code_blocks[0], ("python", " code2 \n"))
        self.assertEqual(code_blocks[1], ("javascript", "code3"))

     def test_extract_keywords(self):
        query = "This is a Test Query, with SOME words."
        keywords = extract_keywords(query)
        self.assertEqual(keywords, "this is a test query with some words")

        query = "!@#$%^"
        keywords = extract_keywords(query)
        self.assertEqual(keywords, "")
    
     @patch('main.google_search')
     @patch('main.get_api_response')
     async def test_search_command(self, mock_get_api_response, mock_google_search):
         mock_google_search.return_value = "- [Test](test)\n Test Snippet"
         mock_get_api_response.return_value = ("Test Response", None)
         
         mock_ctx = MagicMock()
         mock_ctx.channel.id = ALLOWED_CHANNEL_ID
         mock_ctx.message.author.id = 12345
         mock_ctx.send = MagicMock()
         
         query = "test query"
         
         await bot.get_command("timkiem").callback(mock_ctx, query=query)
         
         mock_google_search.assert_called_once()
         mock_get_api_response.assert_called_once()
         mock_ctx.send.assert_called()

         
     @patch('main.google_search')
     async def test_search_no_results(self, mock_google_search):
        mock_google_search.return_value = None
        mock_ctx = MagicMock()
        mock_ctx.channel.id = ALLOWED_CHANNEL_ID
        mock_ctx.send = MagicMock()
        
        query = "test query"
        
        await bot.get_command("timkiem").callback(mock_ctx, query=query)
        
        mock_google_search.assert_called_once()
        mock_ctx.send.assert_called_once_with("No results found or an error occurred during the search.")
     
     @patch('main.google_search')
     async def test_search_error(self, mock_google_search):
          mock_google_search.side_effect = Exception("Test Search Error")
          mock_ctx = MagicMock()
          mock_ctx.channel.id = ALLOWED_CHANNEL_ID
          mock_ctx.send = MagicMock()
          query = "test query"

          await bot.get_command("timkiem").callback(mock_ctx, query=query)
          
          mock_google_search.assert_called_once()
          mock_ctx.send.assert_called_once()
          self.assert_log_contains("Error during search: Test Search Error")
     
     @patch('main.get_api_response')
     async def test_process_message(self, mock_get_api_response):
        mock_get_api_response.return_value = ("Test Response", None)
        mock_message = MagicMock()
        mock_message.author = MagicMock()
        mock_message.author.id = 123
        mock_message.author.bot = False
        mock_message.channel.id = ALLOWED_CHANNEL_ID
        mock_message.content = "Test message"
        mock_thinking_message = MagicMock()
        mock_thinking_message.delete = MagicMock()
        
        await process_message(mock_message, mock_thinking_message)
        
        mock_get_api_response.assert_called()
        mock_thinking_message.delete.assert_called()

     @patch('main.get_api_response')
     async def test_process_message_error(self, mock_get_api_response):
        mock_get_api_response.return_value = (None, "API Error")
        mock_message = MagicMock()
        mock_message.author = MagicMock()
        mock_message.author.id = 123
        mock_message.author.bot = False
        mock_message.channel.id = ALLOWED_CHANNEL_ID
        mock_message.content = "Test message"
        mock_message.channel.send = MagicMock()
        mock_thinking_message = MagicMock()
        mock_thinking_message.delete = MagicMock()
        
        await process_message(mock_message, mock_thinking_message)

        mock_message.channel.send.assert_called_once_with(content="Error: API Error", reference=mock_message)
        mock_thinking_message.delete.assert_not_called()
        self.assert_log_contains("Error: API Error")

     async def test_send_long_message(self):
         mock_channel = MagicMock()
         mock_channel.send = MagicMock()
         long_message = "A " * 3000  # Create a long message exceeding 2000 characters
         processing_time = 1.23
         footer = await create_footer(processing_time, "long response")
         full_message = f"{long_message}\n{footer}"
         
         await send_long_message(mock_channel, full_message)
         
         mock_channel.send.assert_called()
         self.assertGreater(mock_channel.send.call_count, 1)

     async def test_send_long_message_with_sentences(self):
         mock_channel = MagicMock()
         mock_channel.send = MagicMock()
         long_message = "This is sentence one. This is sentence two? This is sentence three. " * 100
         processing_time = 1.23
         footer = await create_footer(processing_time, "long response")
         full_message = f"{long_message}\n{footer}"
         
         await send_long_message(mock_channel, full_message)
         
         mock_channel.send.assert_called()
         self.assertGreater(mock_channel.send.call_count, 1)

     async def test_send_long_message_no_split(self):
         mock_channel = MagicMock()
         mock_channel.send = MagicMock()
         short_message = "This is a short message"
         processing_time = 1.23
         footer = await create_footer(processing_time, "short message")
         full_message = f"{short_message}\n{footer}"
         await send_long_message(mock_channel, full_message)
         mock_channel.send.assert_called_once()

     def test_context_memory(self):
         key = (123, 456)
         
         CONTEXT_MEMORY[key].append("First message")
         CONTEXT_MEMORY[key].append("First response")
         CONTEXT_MEMORY[key].append("Second message")
         CONTEXT_MEMORY[key].append("Second response")

         self.assertEqual(len(CONTEXT_MEMORY[key]), 4)

         CONTEXT_MEMORY[key].extend([f"Message {i}" for i in range(10)])
         self.assertEqual(len(CONTEXT_MEMORY[key]), 14)

     @patch('main.asyncio.get_running_loop')
     async def test_stop_bot(self, mock_loop):
        
        mock_loop_instance = MagicMock()
        mock_loop.return_value = mock_loop_instance
        
        mock_bot_close = MagicMock()
        bot.close = mock_bot_close
        
        _stop_future.set_result(True)
        await stop_bot()
        
        mock_bot_close.assert_called_once()
        self.assert_log_contains("Stopping the bot...")
        self.assert_log_contains("Bot has stopped.")

if __name__ == '__main__':
    unittest.main()
