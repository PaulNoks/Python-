#!/usr/bin/env python3
"""
AI Helpdesk Bot
Telegram bot for customer support with AI-powered responses
"""

import os
import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

class AIHelpdeskBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.context_file = "user_contexts.json"
        self.load_contexts()
    
    def load_contexts(self):
        """Load user conversation contexts"""
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                self.user_contexts = json.load(f)
        except FileNotFoundError:
            self.user_contexts = {}
    
    def save_contexts(self):
        """Save user conversation contexts"""
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_contexts, f, ensure_ascii=False, indent=2)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_name = update.effective_user.first_name or "пользователь"
        welcome_message = f"""
🤖 Добро пожаловать, {user_name}!

Я AI-бот службы поддержки. Могу помочь вам с:
• Техническими вопросами
• Информацией о продуктах/услугах  
• Решением проблем
• Общими консультациями

Просто напишите ваш вопрос, и я постараюсь помочь!

Команды:
/help - справка
/clear - очистить контекст беседы
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📋 Доступные команды:

/start - начать работу с ботом
/help - показать эту справку
/clear - очистить историю нашего разговора

💡 Как пользоваться:
• Просто напишите свой вопрос
• Я запоминаю контекст разговора
• Могу помочь с техническими и общими вопросами
• Отвечаю на русском и английском языках

Если не понимаю вопрос, попробуйте переформулировать его.
        """
        await update.message.reply_text(help_text)
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command - clear user context"""
        user_id = str(update.effective_user.id)
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
            self.save_contexts()
        await update.message.reply_text("🔄 История разговора очищена. Начнем с чистого листа!")
    
    def get_ai_response(self, user_message: str, user_id: str) -> str:
        """Get AI response from OpenAI"""
        try:
            # Get or initialize user context
            if user_id not in self.user_contexts:
                self.user_contexts[user_id] = []
            
            # Add system message for helpdesk context
            messages = [
                {
                    "role": "system", 
                    "content": """Ты AI-ассистент службы поддержки. Отвечай вежливо, профессионально и по делу. 
                    Если не знаешь ответ, честно признавайся и предлагай обратиться к специалисту.
                    Отвечай на том языке, на котором задан вопрос."""
                }
            ]
            
            # Add conversation history (last 10 messages)
            messages.extend(self.user_contexts[user_id][-10:])
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Get AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Update context
            self.user_contexts[user_id].append({"role": "user", "content": user_message})
            self.user_contexts[user_id].append({"role": "assistant", "content": ai_response})
            
            # Keep only last 20 messages to manage context size
            if len(self.user_contexts[user_id]) > 20:
                self.user_contexts[user_id] = self.user_contexts[user_id][-20:]
            
            self.save_contexts()
            return ai_response
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте еще раз или обратитесь к администратору."
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_id = str(update.effective_user.id)
        user_message = update.message.text
        
        logger.info(f"User {user_id}: {user_message}")
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        # Get AI response
        ai_response = self.get_ai_response(user_message, user_id)
        
        # Send response
        await update.message.reply_text(ai_response)
        
        logger.info(f"Bot response to {user_id}: {ai_response[:100]}...")
    
    def run(self):
        """Run the bot"""
        logger.info("Starting AI Helpdesk Bot...")
        
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("clear", self.clear_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start bot
        logger.info("Bot is running... Press Ctrl+C to stop")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Main function"""
    try:
        bot = AIHelpdeskBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise

if __name__ == "__main__":
    main()