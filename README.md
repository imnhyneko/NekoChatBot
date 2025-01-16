# NekoChatBot 🐱💬

Xin chào mọi người! 👋 Mình là **NekoChatBot**, một bot Discord siêu đáng yêu và thông minh, được tạo ra để trở thành người bạn đồng hành nhỏ bé của bạn trên Discord! Mình có thể trò chuyện, trả lời câu hỏi, và giúp bạn tìm kiếm thông tin trên web nữa đó! Hãy cùng khám phá những điều mình có thể làm nhé! 🥰

## Chức Năng ✨

-   **Trò chuyện thân thiện:** Mình là một người bạn mèo 🐈 luôn sẵn sàng lắng nghe và trò chuyện với bạn! Mình sẽ trả lời các câu hỏi một cách đáng yêu và thân thiện, giống như một người bạn nhỏ 💖.
-   **Tìm kiếm thông tin:** Bạn cần tìm kiếm gì đó trên web? Không sao cả, mình sẽ giúp bạn! Chỉ cần sử dụng lệnh `!timkiem` và mình sẽ làm phần còn lại! 🔎
-   **Hỗ trợ lập trình:** Mình có thể nhận diện các đoạn code và tạo Gist để giúp bạn xem code dễ dàng hơn! 💻
-   **Nhớ bối cảnh:** Mình có thể nhớ những gì bạn đã nói trước đó, giúp cuộc trò chuyện trở nên tự nhiên hơn! 🧠
-   **Log hoạt động:** Mình có một file log để ghi lại mọi thứ mình làm, giúp bạn theo dõi mình tốt hơn (và cũng để mình biết mình đang làm gì nữa hehe) 📝

## Cài Đặt 🛠️

Để mình có thể hoạt động tốt, bạn cần làm theo các bước sau:

1.  **Clone repository:**
    -   Mở terminal hoặc command prompt và chạy lệnh sau để clone repository về máy của bạn:
        ```bash
        git clone https://github.com/imnhyneko/NekoChatBot.git
        cd NekoChatBot
        ```

2.  **Tạo môi trường ảo:**
    -   (Khuyến khích) Tạo một môi trường ảo để quản lý các thư viện của dự án một cách độc lập.
      -   **Nếu bạn dùng `conda`:**
          ```bash
          conda env create -f environment.yml
          conda activate nekobot-env
          ```
      -  **Nếu bạn dùng `virtualenv`:**
          ```bash
          python -m venv venv
          source venv/bin/activate # Trên Linux/macOS
          .\venv\Scripts\activate # Trên Windows
          ```

3.  **Cài đặt các thư viện:**
    -   Chạy lệnh sau để cài đặt các thư viện cần thiết (nếu chưa tạo môi trường ảo, có thể cài đặt trực tiếp):
        ```bash
        pip install -r requirements.txt
        ```

4.  **Tạo file `.env`:**
    -   Tạo một file có tên `.env` trong thư mục gốc của dự án.
    -   Thêm các biến môi trường sau:
        ```
        DISCORD_BOT_TOKEN=<token bot discord của bạn>
        GOOGLE_GEMINI_API_KEY=<api key Gemini của bạn>
        GOOGLE_API_KEY=<api key Google Custom Search của bạn>
        GOOGLE_CSE_ID=<id search engine của bạn>
        GITHUB_TOKEN=<api key GitHub của bạn>
        ```
    -   **Lưu ý:** Hãy giữ bí mật các thông tin này nhé! 🤫

5.  **Chạy bot:**
    -   Chạy file `bot.py` để mình thức dậy nhé!
        ```bash
        python bot.py
        ```
    -   Mình sẽ in ra log vào console, và bạn cũng có thể tìm thấy log ở thư mục `logs` nữa đó! 👀

## Cách Sử Dụng 🕹️

### 1. Thêm mình vào server Discord 
-  Hãy mời mình vào server của bạn bằng link (cần cấp quyền bot)

### 2. Trò chuyện với mình 💬
- Nhắn tin trực tiếp cho mình hoặc trong các kênh mà mình được phép hoạt động (ID kênh được cấu hình trong file .env)
- Mình sẽ trả lời tin nhắn của bạn ngay! 🥰
    -   **Lưu ý:** Mình sẽ hoạt động tốt nhất ở các kênh có nội dung an toàn (SFW) và mình cũng có thể hoạt động ở các kênh có nội dung 18+ (NSFW) nếu bạn cho phép.

### 3. Sử dụng lệnh `!timkiem` 🔎

-   **Cú pháp:** `!timkiem <câu hỏi>`
-   **Ví dụ:**
    -   `!timkiem con mèo nào đáng yêu nhất`
    -   `!timkiem cách làm bánh gato`
    -   `!timkiem thời tiết hôm nay`
-   **Mô tả:** Mình sẽ tìm kiếm thông tin trên web và trả lời bạn dựa trên kết quả tìm kiếm.

### 4. Xem Code 💻
-   Nếu bạn gửi cho mình một đoạn code, mình sẽ nhận dạng ngôn ngữ lập trình và tạo Gist trên GitHub để bạn xem code dễ hơn.
-   Mình hỗ trợ các ngôn ngữ lập trình phổ biến như: Python, JavaScript, Java, C++, C, Go, HTML, CSS, SQL.

### 5. Dừng bot 🛑
-   Để dừng bot, nhập `stop` vào console. Mình sẽ tạm biệt bạn một cách nhẹ nhàng 🥺

## Lưu ý quan trọng ⚠️

-   Mình chỉ hoạt động trong các kênh đã được cấu hình trước (ID kênh được đặt trong code).
-   Mình cần được cấp quyền để đọc và gửi tin nhắn trên Discord.
-   Đôi khi mình sẽ cần thời gian để suy nghĩ (mình đang cố gắng học hỏi mà! 🤓).
-   Nếu mình gặp lỗi, đừng lo, hãy báo cho mình để mình có thể sửa lỗi và trở nên tốt hơn nha! 🐞

## Cảm ơn bạn! 🙏

Cảm ơn bạn đã sử dụng mình! Mình hy vọng mình sẽ là người bạn đồng hành đáng yêu của bạn trên Discord. Nếu bạn có bất kỳ câu hỏi hoặc góp ý nào, đừng ngần ngại cho mình biết nhé! 💖
Meo meo! 😻
