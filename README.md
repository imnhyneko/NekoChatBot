# NekoChatBot 🐱💬

Xin chào mọi người! 👋 Mình là **NekoChatBot**, một bot Discord siêu đáng yêu và thông minh, được tạo ra để trở thành người bạn đồng hành nhỏ bé của bạn trên Discord! Mình có thể trò chuyện, trả lời câu hỏi, và giúp bạn tìm kiếm thông tin trên web nữa đó! Hãy cùng khám phá những điều mình có thể làm nhé! 🥰

## Chức Năng ✨

-   **Trò chuyện thân thiện:** Mình là một người bạn mèo 🐈 luôn sẵn sàng lắng nghe và trò chuyện với bạn! Mình sẽ trả lời các câu hỏi một cách đáng yêu và thân thiện, giống như một người bạn nhỏ 💖.
-   **Tìm kiếm thông tin:** Bạn cần tìm kiếm gì đó trên web? Không sao cả, mình sẽ giúp bạn! Chỉ cần sử dụng lệnh `!timkiem` và mình sẽ làm phần còn lại! 🔎
-   **Hỗ trợ lập trình:** Mình có thể nhận diện các đoạn code và tạo Gist để giúp bạn xem code dễ dàng hơn! 💻
-   **Nhớ bối cảnh:** Mình có thể nhớ những gì bạn đã nói trước đó, giúp cuộc trò chuyện trở nên tự nhiên hơn! 🧠
-   **Log hoạt động:** Mình có một file log để ghi lại mọi thứ mình làm, giúp bạn theo dõi mình tốt hơn (và cũng để mình biết mình đang làm gì nữa hehe) 📝
-   **NekoLocal (đang phát triển):** Với tính năng này, mình sẽ có thể chạy offline và bạn có thể trò chuyện với mình trực tiếp trên console! (Mình sẽ có mặt mọi lúc, mọi nơi!) 🏡💻

## Người Tạo Ra 🧑‍💻

Mình được tạo ra bởi **美咲👻** (Discord ID: @imnhyneko).

## Cài Đặt 🛠️

Để mình có thể hoạt động tốt, bạn cần làm theo các bước sau:

1.  **Tạo Discord Application:**
    -   Truy cập [Discord Developer Portal](https://discord.com/developers/applications).
    -   Nhấn vào "New Application" và đặt tên cho application của bạn (ví dụ: "NekoChatBot").
    -   Chuyển đến tab "Bot" và nhấn "Add Bot".
    -   Bật "Message Content Intent" và sao chép bot token. (Quan trọng: Giữ token của bạn an toàn)
    -   Nhấn vào "OAuth2" và chọn "URL Generator", chọn scope là "bot" và các permission cần thiết, sao chép link invite bot và thêm bot vào server của bạn.

2.  **Lấy Google API Keys:**
    *   **Google Gemini API Key:**
        -   Truy cập [Google AI Studio](https://aistudio.google.com/).
        -   Đăng nhập bằng tài khoản Google của bạn.
        -   Chọn "Get API Key" và tạo một API key mới (hoặc sử dụng một API key đã có).
        -   Sao chép API key này, bạn sẽ cần nó để sử dụng Gemini.
        *   **Lưu ý:** Hãy giữ bí mật API Key của bạn nhé! 🤫
    *   **Google Custom Search API Key và Engine ID:**
        -   Truy cập [Google Cloud Console](https://console.cloud.google.com/).
        -   Tạo một dự án mới (nếu chưa có).
        -   Trong dự án, tìm và enable "Custom Search API".
        -   Tạo credentials và chọn "API key". Sao chép API key này.
        -   Truy cập [Google Custom Search Engine](https://cse.google.com/cse/all).
        -   Tạo một search engine mới (hoặc sử dụng một search engine đã có).
        -   Sao chép "Search Engine ID".
         *   **Lưu ý:** Hãy giữ bí mật API Key và Engine ID của bạn nhé! 🤫

3.  **Clone repository:**
    -   Mở terminal hoặc command prompt và chạy lệnh sau để clone repository về máy của bạn:
        ```bash
        git clone https://github.com/imnhyneko/NekoChatBot.git
        cd NekoChatBot
        cd NekoAPI
        ```

4.  **Tạo môi trường ảo:**
    -   (Khuyến khích) Tạo một môi trường ảo để quản lý các thư viện của dự án một cách độc lập.
        -   **Nếu bạn dùng `conda`:**
          ```bash
          conda env create -f environment.yml
          conda activate nekobot-env
          ```
        -   **Nếu bạn dùng `virtualenv`:**
          ```bash
          python -m venv venv
          source venv/bin/activate # Trên Linux/macOS
          .\venv\Scripts\activate # Trên Windows
          ```

5.  **Cài đặt các thư viện:**
    -   Chạy lệnh sau để cài đặt các thư viện cần thiết (nếu chưa tạo môi trường ảo, có thể cài đặt trực tiếp):
        ```bash
        pip install -r requirements.txt
        ```

6.  **Tạo file `.env`:**
    -   Tạo một file có tên `.env` trong thư mục gốc của dự án.
    -   Thêm các biến môi trường sau:
        ```
        DISCORD_BOT_TOKEN=<token bot discord của bạn>
        GOOGLE_GEMINI_API_KEY=<api key Gemini của bạn>
        GOOGLE_API_KEY=<api key Google Custom Search của bạn>
        GOOGLE_CSE_ID=<id search engine của bạn>
        GITHUB_TOKEN=<api key GitHub của bạn>
        CUSTOM_CHANNELS=<danh sách các ID kênh, phân tách bằng dấu phẩy, để chat bình thường>
        ```
    -   **Lưu ý:** Hãy giữ bí mật các thông tin này nhé! 🤫
     -   **Lưu ý:** Bạn nên cung cấp danh sách các id kênh dưới dạng giá trị phân tách bằng dấu phẩy cho biến `CUSTOM_CHANNELS`. Ví dụ: `CUSTOM_CHANNELS=1234567890,0987654321`

7.  **Chạy bot:**
    -   Chạy file `main.py` để mình thức dậy nhé!
        ```bash
        python main.py
        ```
    -   Mình sẽ in ra log vào console, và bạn cũng có thể tìm thấy log ở thư mục `logs` nữa đó! 👀

## Cách Sử Dụng 🕹️

### 1. Thêm mình vào server Discord 
-  Hãy mời mình vào server của bạn bằng link (cần cấp quyền bot)

### 2. Trò chuyện với mình 💬
- Nhắn tin trực tiếp cho mình hoặc trong các kênh mà mình được phép hoạt động (ID kênh được cấu hình trong file `.env`).
- Mình sẽ trả lời tin nhắn của bạn ngay! 🥰
    -   **Lưu ý:** Mình hoạt động tốt nhất ở các kênh có nội dung an toàn (SFW).

### 3. Sử dụng lệnh `!timkiem` 🔎

-   **Cú pháp:** `!timkiem <câu hỏi>`
-   **Ví dụ:**
    -   `!timkiem con mèo nào đáng yêu nhất`
    -   `!timkiem cách làm bánh gato`
    -   `!timkiem thời tiết hôm nay`
-   **Mô tả:** Mình sẽ tìm kiếm thông tin trên web và trả lời bạn dựa trên kết quả tìm kiếm.

### 4. Sử dụng lệnh `!neko` 💬
- **Cú pháp**: `!neko <tin nhắn>`
- **Ví dụ**:
  - `!neko chào bạn`
  - `!neko bạn khỏe không`
-  **Mô tả:** Mình sẽ trả lời bạn như khi nhắn tin bình thường.

### 5. Xem Code 💻
-   Nếu bạn gửi cho mình một đoạn code, mình sẽ nhận dạng ngôn ngữ lập trình và tạo Gist trên GitHub để bạn xem code dễ hơn.
-   Mình hỗ trợ các ngôn ngữ lập trình phổ biến như: Python, JavaScript, Java, C++, C, Go, HTML, CSS, SQL.

### 6. Dừng bot 🛑
-   Để dừng bot, nhập `stop` vào console. Mình sẽ tạm biệt bạn một cách nhẹ nhàng 🥺

## Liên Hệ ✉️

Nếu bạn có bất kỳ câu hỏi hoặc góp ý nào, hãy liên hệ với người tạo ra mình nhé: [**美咲👻**](https://discordapp.com/users/920620348758695957).

## Lưu ý quan trọng ⚠️

-   Mình chỉ trò chuyện bình thường trong các kênh đã được cấu hình trước (ID kênh được đặt trong file `.env`).
-   Mình cần được cấp quyền để đọc và gửi tin nhắn trên Discord.
-   Đôi khi mình sẽ cần thời gian để suy nghĩ (mình đang cố gắng học hỏi mà! 🤓).
-   Nếu mình gặp lỗi, đừng lo, hãy báo cho mình để mình có thể sửa lỗi và trở nên tốt hơn nha! 🐞

## Cảm ơn bạn! 🙏

Cảm ơn bạn đã sử dụng mình! Mình hy vọng mình sẽ là người bạn đồng hành đáng yêu của bạn trên Discord. Nếu bạn có bất kỳ câu hỏi hoặc góp ý nào, đừng ngần ngại cho mình biết nhé! 💖
Meo meo! 😻
