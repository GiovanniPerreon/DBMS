from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from typing import List, Optional
import re

class FreeReadingAI:
    """
    A completely free Reading AI using Hugging Face transformers
    No API keys required - runs locally
    """
    
    def __init__(self):
        print("Initializing Free Reading AI...")
        print("Loading models (this may take a few minutes on first run)...")
        
        # Initialize models
        try:
            # For summarization
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            
            # For question answering
            self.qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
            
            # For text classification (sentiment, etc.)
            self.classifier = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
            
            print("✓ Models loaded successfully!")
            
        except Exception as e:
            print(f"Error loading models: {e}")
            print("Make sure you have internet connection for first-time model download")
    
    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """
        Summarize text using BART model
        """
        try:
            # BART works best with texts between 50-1024 tokens
            if len(text.split()) < 10:
                return "Text too short to summarize effectively."
            
            # Truncate if too long (BART has token limits)
            words = text.split()
            if len(words) > 500:
                text = " ".join(words[:500]) + "..."
            
            result = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            return result[0]['summary_text']
            
        except Exception as e:
            return f"Error summarizing: {str(e)}"
    
    def answer_questions(self, text: str, question: str) -> str:
        """
        Answer questions about the text using DistilBERT
        """
        try:
            result = self.qa_pipeline(question=question, context=text)
            confidence = result['score']
            answer = result['answer']
            
            if confidence > 0.1:
                return f"{answer} (confidence: {confidence:.2f})"
            else:
                return "I couldn't find a confident answer to that question in the text."
                
        except Exception as e:
            return f"Error answering question: {str(e)}"
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze the sentiment/tone of the text
        """
        try:
            result = self.classifier(text)
            label = result[0]['label']
            score = result[0]['score']
            
            # Convert labels to more readable format
            sentiment_map = {
                'LABEL_0': 'Negative',
                'LABEL_1': 'Neutral', 
                'LABEL_2': 'Positive'
            }
            
            sentiment = sentiment_map.get(label, label)
            return f"Sentiment: {sentiment} (confidence: {score:.2f})"
            
        except Exception as e:
            return f"Error analyzing sentiment: {str(e)}"
    
    def calculate_reading_stats(self, text: str) -> str:
        """
        Calculate basic reading statistics
        """
        try:
            # Basic text statistics
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            word_count = len(words)
            sentence_count = len(sentences)
            avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
            
            # Character count
            char_count = len(text)
            char_count_no_spaces = len(text.replace(' ', ''))
            
            # Estimated reading time (average 200 words per minute)
            reading_time_minutes = word_count / 200
            
            # Simple vocabulary complexity (percentage of long words)
            long_words = [w for w in words if len(w) > 6]
            complexity_ratio = len(long_words) / word_count if word_count > 0 else 0
            
            stats = f"""
📊 Reading Statistics:
• Words: {word_count}
• Sentences: {sentence_count}
• Characters: {char_count} ({char_count_no_spaces} without spaces)
• Average words per sentence: {avg_words_per_sentence:.1f}
• Estimated reading time: {reading_time_minutes:.1f} minutes
• Vocabulary complexity: {complexity_ratio:.1%} long words (6+ letters)
• Estimated difficulty: {'High' if avg_words_per_sentence > 20 or complexity_ratio > 0.3 else 'Medium' if avg_words_per_sentence > 15 or complexity_ratio > 0.2 else 'Easy'}
            """
            
            return stats.strip()
            
        except Exception as e:
            return f"Error calculating stats: {str(e)}"
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases using simple heuristics
        """
        try:
            words = text.split()
            
            # Find capitalized words (potential proper nouns)
            proper_nouns = []
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word)
                if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                    if clean_word.lower() not in ['the', 'and', 'but', 'for', 'are', 'this', 'that']:
                        proper_nouns.append(clean_word)
            
            # Find repeated words (might be important)
            word_freq = {}
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word.lower())
                if len(clean_word) > 3:  # Only count words longer than 3 characters
                    word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
            
            # Get most frequent words
            frequent_words = [word for word, freq in word_freq.items() if freq > 1]
            frequent_words.sort(key=lambda x: word_freq[x], reverse=True)
            
            # Combine and deduplicate
            key_phrases = list(set(proper_nouns[:5] + frequent_words[:5]))
            
            return key_phrases[:10]  # Return top 10
            
        except Exception as e:
            return [f"Error extracting phrases: {str(e)}"]
    
    def generate_simple_questions(self, text: str) -> List[str]:
        """
        Generate simple comprehension questions using template-based approach
        """
        try:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 3]
            
            questions = []
            
            # Generate different types of questions
            question_templates = [
                "What does the text say about {}?",
                "According to the text, what is {}?",
                "How is {} described in the passage?",
                "What information is provided about {}?",
                "Why is {} mentioned in the text?"
            ]
            
            key_phrases = self.extract_key_phrases(text)
            
            for i, phrase in enumerate(key_phrases[:3]):
                if i < len(question_templates):
                    questions.append(question_templates[i].format(phrase.lower()))
            
            # Add some general questions
            general_questions = [
                "What is the main topic of this text?",
                "What are the key points mentioned?",
                "What conclusion can you draw from this passage?"
            ]
            
            questions.extend(general_questions[:2])
            
            return questions[:5]  # Return top 5 questions
            
        except Exception as e:
            return [f"Error generating questions: {str(e)}"]

def main_free():
    """
    Demo function for the free Reading AI
    """
    print("=== Free Reading AI Demo ===")
    print("🚀 No API keys required - runs completely locally!")
    print("📦 Models will be downloaded on first run (may take a few minutes)")
    print()
    
    # Initialize the AI
    ai = FreeReadingAI()
    
    # Sample text
    sample_text = """
    Climate change refers to long-term shifts in global temperatures and weather patterns. While climate variations are natural, human activities have been the main driver of climate change since the 1800s. The burning of fossil fuels like coal, oil, and gas produces greenhouse gases that trap heat in Earth's atmosphere. This leads to rising temperatures, melting ice caps, and more extreme weather events. Scientists agree that immediate action is needed to reduce greenhouse gas emissions and limit global warming to prevent catastrophic environmental changes.
    """
    
    print("Sample text loaded. Choose an option:")
    print("1. Summarize text")
    print("2. Ask a question about the text")
    print("3. Analyze sentiment/tone")
    print("4. Calculate reading statistics")
    print("5. Extract key phrases")
    print("6. Generate comprehension questions")
    print("7. Use your own text")
    print("0. Exit")
    
    while True:
        choice = input("\nEnter your choice (0-7): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            print("\n--- Text Summary ---")
            summary = ai.summarize_text(sample_text)
            print(summary)
        elif choice == '2':
            question = input("Enter your question about the text: ")
            print(f"\n--- Answer ---")
            answer = ai.answer_questions(sample_text, question)
            print(answer)
        elif choice == '3':
            print("\n--- Sentiment Analysis ---")
            sentiment = ai.analyze_sentiment(sample_text)
            print(sentiment)
        elif choice == '4':
            print("\n--- Reading Statistics ---")
            stats = ai.calculate_reading_stats(sample_text)
            print(stats)
        elif choice == '5':
            print("\n--- Key Phrases ---")
            phrases = ai.extract_key_phrases(sample_text)
            for i, phrase in enumerate(phrases, 1):
                print(f"{i}. {phrase}")
        elif choice == '6':
            print("\n--- Comprehension Questions ---")
            questions = ai.generate_simple_questions(sample_text)
            for i, q in enumerate(questions, 1):
                print(f"{i}. {q}")
        elif choice == '7':
            print("Enter your text (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            sample_text = "\n".join(lines[:-1])
            print("Text updated! You can now use options 1-6 with your text.")
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # Run the free version by default
    main_free()
