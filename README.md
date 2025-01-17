# NekoChatBot 🐱💬

Hello! 👋 I'm **NekoChatBot**, a smart and helpful Discord bot designed to be your companion on Discord! I can chat, answer questions, and help you search for information on the web. Let's explore what I can offer! 😊

## Features ✨

-   **Natural Conversation:** I can interact and chat with you naturally, providing responses and assistance as requested.
-   **Information Search:** You can use the `!search` command to have me help you find information on the web.
-   **Programming Support:** I can identify and create Gists from code snippets, making it easier to share and view code.
-   **Contextual Memory:** I can remember previous messages to provide relevant and continuous responses during conversations.
-   **Activity Logging:** All my activities are logged in a log file, allowing you to easily track and manage my actions.
-   **NekoLocal (Under Development):** This feature will enable me to operate offline on the console, letting you interact with me anytime, anywhere.

## Developer 🧑‍💻

I was developed by [**美咲👻**](https://discordapp.com/users/920620348758695957) (Discord ID: @imnhyneko).

## Installation Guide 🛠️

To get me up and running, please follow these steps:

1.  **Create a Discord Application:**
    -   Go to the [Discord Developer Portal](https://discord.com/developers/applications).
    -   Click "New Application" and give it a name (e.g., "NekoChatBot").
    -   Navigate to the "Bot" tab and select "Add Bot".
    -   Enable "Message Content Intent" and copy your bot token (Note: Keep your token secure).
    -   In "OAuth2" -> "URL Generator," select the "bot" scope, required permissions, copy the bot invite link, and add the bot to your server.

2.  **Obtain Google API Keys:**
    *   **Google Gemini API Key:**
        -   Go to [Google AI Studio](https://aistudio.google.com/).
        -   Sign in with your Google account.
        -   Select "Get API Key" and create a new key or use an existing one.
        -   Copy this API key (Secure your API key).
    *   **Google Custom Search API Key and Engine ID:**
        -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
        -   Create a new project (if you don't already have one).
        -   Enable the "Custom Search API".
        -   Create credentials and select "API key". Copy this API key.
        -   Go to the [Google Custom Search Engine](https://cse.google.com/cse/all).
        -   Create or use an existing search engine.
        -   Copy the "Search Engine ID" (Secure your API key and Engine ID).

3.  **Clone Repository:**
    -   Open a terminal and run:
        ```bash
        git clone https://github.com/imnhyneko/NekoChatBot.git
        cd NekoChatBot
        cd NekoAPI
        ```

4.  **Create Virtual Environment:**
    -   (Recommended) Create a virtual environment to manage libraries:
        -   **`conda`:**
          ```bash
          conda env create -f environment.yml
          conda activate nekobot-env
          ```
        -   **`virtualenv`:**
          ```bash
          python -m venv venv
          source venv/bin/activate # On Linux/macOS
          .\venv\Scripts\activate # On Windows
          ```

5.  **Install Libraries:**
    -   Run the following command to install the required libraries:
        ```bash
        pip install -r requirements.txt
        ```

6.  **Create `.env` File:**
    -   Create a `.env` file in the root directory of the project.
    -   Add the following environment variables:
        ```
        DISCORD_BOT_TOKEN=<Your Discord bot token>
        GOOGLE_GEMINI_API_KEY=<Your Gemini API key>
        GOOGLE_API_KEY=<Your Google Custom Search API key>
        GOOGLE_CSE_ID=<Your Search Engine ID>
        GITHUB_TOKEN=<Your GitHub API key>
        CUSTOM_CHANNELS=<List of channel IDs, comma-separated, for normal chat>
        ```
     - Provide the list of channel IDs as comma-separated values for the variable `CUSTOM_CHANNELS`. Example: `CUSTOM_CHANNELS=1234567890,0987654321`
    -   (Note: Keep this information secure).

7.  **Run the Bot:**
    -   Run the `main.py` file:
        ```bash
        python main.py
        ```
    -   You will see logs in the console and in the `logs` directory.

## How to Use 🕹️

### 1. Invite the Bot to Your Server
- Use the invite link to add the bot to your server.

### 2. Interact With the Bot 💬
- Send a direct message to the bot or message within the allowed channels (configured in `.env`).
- The bot will respond to your messages.

### 3. Use the `!search` Command 🔎

-   **Syntax:** `!search <query>`
-   **Examples:**
    -   `!search tell me about Độ Mixi`
    -   `!search how to make a cake`
    -   `!search today's weather`
-   **Description:** The bot will search the web for information and respond based on the results.

### 4. Use the `!neko` Command 💬

-   **Syntax:** `!neko <message>`
-   **Examples:**
    -   `!neko hello`
    -   `!neko how are you`
-   **Description:** The bot will reply to your message as in a normal conversation.

### 5. View Code 💻

-   The bot will recognize programming languages and create a GitHub Gist for sent code snippets.
-   Supports: Python, JavaScript, Java, C++, C, Go, HTML, CSS, SQL.

### 6. Stop the Bot 🛑

-   Enter `stop` in the console to stop the bot.

## Contact ✉️

For any questions or suggestions, please contact: [**美咲👻**](https://discordapp.com/users/920620348758695957).

## Important Notes ⚠️

-   The bot only operates in pre-configured channels.
-   The bot requires permissions to read and send messages on Discord.
-   The bot may take some time to process requests.
-   If you encounter any issues, please report them so the bot can be improved.

## Thank You! 🙏

Thank you for using NekoChatBot! I hope I can be a helpful companion on Discord. All feedback is welcome.
