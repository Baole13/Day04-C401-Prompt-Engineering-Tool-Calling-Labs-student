import os
import streamlit as st
from dotenv import load_dotenv
from agent import ResearchAgent
from providers.gemini_provider import GeminiProvider
from tools import TOOL_FUNCTIONS, load_tool_declarations

# 1. Nạp biến môi trường
load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    st.error("Lỗi: Không tìm thấy GEMINI_API_KEY. Vui lòng kiểm tra file .env")
    st.stop()

st.title("🤖 AI Research Assistant")

# 2. Khởi tạo Agent
if "agent" not in st.session_state:
    with open("artifacts/system_prompt.md", "r", encoding="utf-8") as f:
        prompt = f.read()
    
    # Load declarations để Agent biết cách gọi tool
    tool_declarations = load_tool_declarations("artifacts/tools.yaml")
    
    st.session_state.agent = ResearchAgent(
        provider=GeminiProvider(),
        system_prompt=prompt,
        tools=tool_declarations
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Hiển thị lịch sử chat lên giao diện Streamlit
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Xử lý Input từ người dùng
if user_input := st.chat_input("Bạn muốn nghiên cứu gì hôm nay?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        # Tạo mảng tin nhắn thô để truyền vào agent.run()
        # SDK Gemini yêu cầu cấu hình hội thoại chặt chẽ thông qua chuỗi văn bản liên tục
        messages = [{"role": "user", "content": user_input}]
        
        with st.spinner("Đang suy nghĩ..."):
            # Lần gọi Agent thứ nhất: Trợ lý quyết định xem có gọi tool hay không
            agent_run = st.session_state.agent.run(messages)
            
            # Nếu Agent muốn gọi Tool
            if agent_run.tool_calls:
                for call in agent_run.tool_calls:
                    tool_name = call.name
                    tool_args = call.args
                    
                    if tool_name in TOOL_FUNCTIONS:
                        st.info(f"🛠 Đang gọi tool: {tool_name} với tham số {tool_args}")
                        
                        # Thực thi hàm Python tương ứng
                        tool_func = TOOL_FUNCTIONS[tool_name]
                        result = tool_func(**tool_args)
                        
                        # HIỂN THỊ TRỰC TIẾP LÊN STREAMLIT ĐỂ THEO DÕI
                        st.write(f"Kết quả thực tế từ hệ thống: `{result}`")
                        
                        # ĐỔI CHIẾN THUẬT NGỮ CẢNH: Để tránh lỗi cấu trúc 400 Bad Request của SDK,
                        # chúng ta chèn kết quả trực tiếp bằng ngôn ngữ tự nhiên vào luồng tiếp theo
                        # Giúp mô phỏng lại ngữ cảnh môi trường (Environment response simulation)
                        prompt_with_context = (
                            f"[HỆ THỐNG PHẢN HỒI KẾT QUẢ CỦA CÔNG CỤ '{tool_name}']: {result}\n\n"
                            f"Dựa trên thông tin hệ thống vừa cung cấp ở trên, hãy đưa ra câu trả lời "
                            f"hoàn chỉnh và tự nhiên nhất cho người dùng đối với câu hỏi: '{user_input}'"
                        )
                        messages = [{"role": "user", "content": prompt_with_context}]
                    else:
                        st.error(f"Tool '{tool_name}' chưa được đăng ký trong hệ thống!")

                # Gọi lại Agent lần 2 với prompt chứa thông tin kết quả trả về từ tool
                agent_run = st.session_state.agent.run(messages)

            # Xuất văn bản phản hồi cuối cùng lên UI Streamlit
            response = agent_run.text or "Tôi đã hoàn thành xử lý dữ liệu yêu cầu."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})