from PyQt5.QtWidgets import QApplication
import sys
from src.chatbot_logic import ChatBotWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    chatbot = ChatBotWindow()
    chatbot.show()
    sys.exit(app.exec_())
