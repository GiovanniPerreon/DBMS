"""
Discord AI Wrapper - Simple interface for Discord bot integration
"""

from free_reading_ai import FreeReadingAI
from typing import Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

class DiscordReadingAI:
    """
    Simple wrapper for Discord bot integration
    Provides easy text-in, result-out interface
    """
    
    def __init__(self):
        self.ai = None
        self.is_loading = False
        self.is_ready = False
        self._executor = ThreadPoolExecutor(max_workers=2)
        
    def initialize(self):
        """Initialize the AI models (call this once when bot starts)"""
        if self.is_loading or self.is_ready:
            return
            
        self.is_loading = True
        print("🤖 Loading AI models for Discord bot...")
        
        try:
            self.ai = FreeReadingAI()
            self.is_ready = True
            self.is_loading = False
            print("✅ AI ready for Discord!")
        except Exception as e:
            print(f"❌ Failed to load AI: {e}")
            self.is_loading = False
            self.is_ready = False
    
    async def initialize_async(self):
        """Async version for Discord bot startup"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self.initialize)
    
    def process_text(self, text: str, action: str = "smart") -> Dict:
        """
        Main function for Discord bot - process text and return results
        
        Args:
            text: Input text to process
            action: What to do with the text
                   - "smart" (default): Auto-choose best action
                   - "summarize": Create summary
                   - "question": Answer a question about text
                   - "sentiment": Analyze tone
                   - "stats": Get reading statistics
                   - "phrases": Extract key phrases
                   - "questions": Generate questions
        
        Returns:
            Dict with 'result' and 'type' keys
        """
        if not self.is_ready:
            return {
                "result": "❌ AI is not ready yet. Please wait for models to load.",
                "type": "error"
            }
        
        if not text or len(text.strip()) < 10:
            return {
                "result": "❌ Please provide more text (at least 10 characters).",
                "type": "error"
            }
        
        try:
            if action == "smart":
                return self._smart_process(text)
            elif action == "summarize":
                return self._summarize(text)
            elif action == "sentiment":
                return self._analyze_sentiment(text)
            elif action == "stats":
                return self._get_stats(text)
            elif action == "phrases":
                return self._extract_phrases(text)
            elif action == "questions":
                return self._generate_questions(text)
            else:
                return {
                    "result": f"❌ Unknown action: {action}",
                    "type": "error"
                }
                
        except Exception as e:
            return {
                "result": f"❌ Error processing text: {str(e)}",
                "type": "error"
            }
    
    async def process_text_async(self, text: str, action: str = "smart") -> Dict:
        """Async version for Discord bot"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.process_text, text, action)
    
    def ask_question(self, text: str, question: str) -> Dict:
        """Ask a specific question about the text"""
        if not self.is_ready:
            return {
                "result": "❌ AI is not ready yet.",
                "type": "error"
            }
        
        try:
            answer = self.ai.answer_questions(text, question)
            return {
                "result": f"**Question:** {question}\n**Answer:** {answer}",
                "type": "answer"
            }
        except Exception as e:
            return {
                "result": f"❌ Error answering question: {str(e)}",
                "type": "error"
            }
    
    async def ask_question_async(self, text: str, question: str) -> Dict:
        """Async version for Discord bot"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.ask_question, text, question)
    
    def _smart_process(self, text: str) -> Dict:
        """Automatically choose the best processing method"""
        word_count = len(text.split())
        
        # For short text, analyze sentiment
        if word_count < 30:
            sentiment = self.ai.analyze_sentiment(text)
            return {
                "result": f"📝 **Text Analysis:**\n{sentiment}",
                "type": "sentiment"
            }
        
        # For medium text, summarize
        elif word_count < 200:
            summary = self.ai.summarize_text(text)
            phrases = self.ai.extract_key_phrases(text)
            key_phrases = ", ".join(phrases[:5]) if phrases else "None found"
            
            return {
                "result": f"📋 **Summary:**\n{summary}\n\n🔑 **Key Topics:** {key_phrases}",
                "type": "summary"
            }
        
        # For long text, provide comprehensive analysis
        else:
            summary = self.ai.summarize_text(text)
            stats = self.ai.calculate_reading_stats(text)
            phrases = self.ai.extract_key_phrases(text)
            key_phrases = ", ".join(phrases[:5]) if phrases else "None found"
            
            return {
                "result": f"📋 **Summary:**\n{summary}\n\n🔑 **Key Topics:** {key_phrases}\n\n{stats}",
                "type": "comprehensive"
            }
    
    def _summarize(self, text: str) -> Dict:
        """Create a summary"""
        summary = self.ai.summarize_text(text)
        return {
            "result": f"📋 **Summary:**\n{summary}",
            "type": "summary"
        }
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment"""
        sentiment = self.ai.analyze_sentiment(text)
        return {
            "result": f"😊 **Sentiment Analysis:**\n{sentiment}",
            "type": "sentiment"
        }
    
    def _get_stats(self, text: str) -> Dict:
        """Get reading statistics"""
        stats = self.ai.calculate_reading_stats(text)
        return {
            "result": f"📊 **Reading Statistics:**\n{stats}",
            "type": "stats"
        }
    
    def _extract_phrases(self, text: str) -> Dict:
        """Extract key phrases"""
        phrases = self.ai.extract_key_phrases(text)
        if phrases:
            phrase_list = "\n".join([f"• {phrase}" for phrase in phrases[:8]])
            return {
                "result": f"🔑 **Key Phrases:**\n{phrase_list}",
                "type": "phrases"
            }
        else:
            return {
                "result": "🔑 **Key Phrases:**\nNo significant phrases found.",
                "type": "phrases"
            }
    
    def _generate_questions(self, text: str) -> Dict:
        """Generate comprehension questions"""
        questions = self.ai.generate_simple_questions(text)
        if questions:
            question_list = "\n".join([f"{i}. {q}" for i, q in enumerate(questions, 1)])
            return {
                "result": f"❓ **Study Questions:**\n{question_list}",
                "type": "questions"
            }
        else:
            return {
                "result": "❓ **Study Questions:**\nCould not generate questions for this text.",
                "type": "questions"
            }
    
    @property
    def status(self) -> str:
        """Get current AI status"""
        if self.is_ready:
            return "✅ Ready"
        elif self.is_loading:
            return "⏳ Loading..."
        else:
            return "❌ Not initialized"

# Example usage for Discord bot:
"""
# In your Discord bot:
from discord_ai_wrapper import DiscordReadingAI

# Initialize once when bot starts
bot_ai = DiscordReadingAI()
await bot_ai.initialize_async()

# Use in commands:
@bot.command()
async def analyze(ctx, *, text):
    result = await bot_ai.process_text_async(text)
    await ctx.send(result['result'])

@bot.command()
async def ask(ctx, question, *, text):
    result = await bot_ai.ask_question_async(text, question)
    await ctx.send(result['result'])
"""
