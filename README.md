# NekoChatBot 🐱💬

Xin chào! 👋 Mình là **NekoChatBot**, một bot Discord thông minh và hữu ích, được thiết kế để trở thành người bạn đồng hành của bạn trên Discord! Mình có khả năng trò chuyện, trả lời câu hỏi, và hỗ trợ tìm kiếm thông tin trên web. Hãy khám phá những gì mình có thể mang lại nhé! 😊

## Chức Năng ✨

-   **Trò Chuyện Tự Nhiên:** Mình có thể tương tác và trò chuyện với bạn một cách tự nhiên, cung cấp phản hồi và hỗ trợ theo yêu cầu.
-   **Tìm Kiếm Thông Tin:** Bạn có thể sử dụng lệnh `!search` để mình giúp bạn tìm kiếm thông tin trên web.
-   **Hỗ Trợ Lập Trình:** Mình có khả năng nhận diện và tạo Gist từ các đoạn code, hỗ trợ việc chia sẻ và xem code một cách thuận tiện.
-   **Ghi Nhớ Bối Cảnh:** Mình có thể ghi nhớ các tin nhắn trước đó để cung cấp phản hồi phù hợp và liên tục trong cuộc trò chuyện.
-   **Ghi Log Hoạt Động:** Mọi hoạt động của mình đều được ghi lại trong file log, giúp bạn dễ dàng theo dõi và quản lý.
-   **NekoLocal (Đang Phát Triển):** Tính năng này sẽ cho phép mình hoạt động offline trên console, giúp bạn tương tác với mình mọi lúc, mọi nơi.

## Người Phát Triển 🧑‍💻

Mình được phát triển bởi **美咲👻** (Discord ID: @imnhyneko).

## Hướng Dẫn Cài Đặt 🛠️

Để mình hoạt động, bạn vui lòng thực hiện theo các bước sau:

1.  **Tạo Discord Application:**
    -   Truy cập [Discord Developer Portal](https://discord.com/developers/applications).
    -   Nhấn "New Application" và đặt tên (ví dụ: "NekoChatBot").
    -   Chuyển đến tab "Bot" và chọn "Add Bot".
    -   Bật "Message Content Intent" và sao chép bot token (Lưu ý: bảo mật token của bạn).
    -   Trong "OAuth2" -> "URL Generator", chọn scope "bot", các permission cần thiết, sao chép link invite bot và thêm bot vào server.

2.  **Lấy Google API Keys:**
    *   **Google Gemini API Key:**
        -   Truy cập [Google AI Studio](https://aistudio.google.com/).
        -   Đăng nhập bằng tài khoản Google.
        -   Chọn "Get API Key" và tạo mới hoặc sử dụng key đã có.
        -   Sao chép API key này (Bảo mật API Key).
    *   **Google Custom Search API Key và Engine ID:**
        -   Truy cập [Google Cloud Console](https://console.cloud.google.com/).
        -   Tạo một dự án mới (nếu chưa có).
        -   Enable "Custom Search API".
        -   Tạo credentials và chọn "API key". Sao chép API key này.
        -   Truy cập [Google Custom Search Engine](https://cse.google.com/cse/all).
        -   Tạo hoặc sử dụng một search engine.
        -   Sao chép "Search Engine ID" (Bảo mật API Key và Engine ID).

3.  **Clone Repository:**
    -   Mở terminal và chạy:
        ```bash
        git clone https://github.com/imnhyneko/NekoChatBot.git
        cd NekoChatBot
        cd NekoAPI
        ```

4.  **Tạo Môi Trường Ảo:**
    -   (Khuyến khích) Tạo một môi trường ảo để quản lý thư viện:
        -   **`conda`:**
          ```bash
          conda env create -f environment.yml
          conda activate nekobot-env
          ```
        -   **`virtualenv`:**
          ```bash
          python -m venv venv
          source venv/bin/activate # Trên Linux/macOS
          .\venv\Scripts\activate # Trên Windows
          ```

5.  **Cài Đặt Thư Viện:**
    -   Chạy lệnh sau để cài đặt các thư viện cần thiết:
        ```bash
        pip install -r requirements.txt
        ```

6.  **Tạo File `.env`:**
    -   Tạo file `.env` trong thư mục gốc dự án.
    -   Thêm các biến môi trường sau:
        ```
        DISCORD_BOT_TOKEN=<bot token Discord>
        GOOGLE_GEMINI_API_KEY=<API key Gemini>
        GOOGLE_API_KEY=<API key Google Custom Search>
        GOOGLE_CSE_ID=<Search Engine ID>
        GITHUB_TOKEN=<API key GitHub>
        CUSTOM_CHANNELS=<danh sách các ID kênh, phân tách bằng dấu phẩy, để chat>
        ```
     -  Cung cấp danh sách các id kênh dưới dạng giá trị phân tách bằng dấu phẩy cho biến `CUSTOM_CHANNELS`. Ví dụ: `CUSTOM_CHANNELS=1234567890,0987654321`
    -   (Lưu ý: Bảo mật thông tin này).

7.  **Chạy Bot:**
    -   Chạy file `main.py`:
        ```bash
        python main.py
        ```
    -   Bạn sẽ thấy log trên console và trong thư mục `logs`.

## Hướng Dẫn Sử Dụng 🕹️

### 1. Mời Bot vào Server
- Sử dụng link mời để thêm bot vào server của bạn.

### 2. Tương Tác Với Bot 💬
- Nhắn tin trực tiếp cho bot hoặc trong các kênh được phép (được cấu hình trong `.env`).
- Bot sẽ phản hồi các tin nhắn của bạn.

### 3. Sử Dụng Lệnh `!search` 🔎

-   **Cú pháp:** `!search <câu hỏi>`
-   **Ví dụ:**
    -   `!search mèo nào đáng yêu nhất`
    -   `!search cách làm bánh gato`
    -   `!search thời tiết hôm nay`
-   **Mô tả:** Bot sẽ tìm kiếm thông tin trên web và trả lời dựa trên kết quả.

### 4. Sử Dụng Lệnh `!neko` 💬

-   **Cú pháp:** `!neko <tin nhắn>`
-   **Ví dụ:**
    -   `!neko chào bạn`
    -   `!neko bạn khỏe không`
-   **Mô tả:** Bot sẽ trả lời tin nhắn của bạn.

### 5. Xem Code 💻

-   Bot sẽ nhận diện và tạo Gist trên GitHub cho các đoạn code được gửi.
-   Hỗ trợ các ngôn ngữ: Python, JavaScript, Java, C++, C, Go, HTML, CSS, SQL.

### 6. Dừng Bot 🛑

-   Nhập `stop` vào console để dừng bot.

## Liên Hệ ✉️

Nếu bạn có bất kỳ câu hỏi hoặc góp ý nào, vui lòng liên hệ: [**美咲👻**](https://discordapp.com/users/920620348758695957).

## Lưu Ý Quan Trọng ⚠️

-   Bot chỉ hoạt động ở các kênh đã được cấu hình.
-   Cần cấp quyền đọc và gửi tin nhắn cho bot.
-   Có thể mất chút thời gian để bot xử lý các yêu cầu.
-   Nếu gặp lỗi, vui lòng báo để bot được cải thiện.

## Cảm ơn! 🙏

Cảm ơn bạn đã sử dụng NekoChatBot! Hy vọng mình sẽ là người bạn hữu ích của bạn trên Discord. Mọi ý kiến đóng góp đều được hoan nghênh.
