import openai
import os
from typing import Optional, List
import json

class ReadingAI:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Reading AI with OpenAI API
        If no API key provided, will try to get from environment variable
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        else:
            print("Warning: No OpenAI API key found. Some features may not work.")
            print("Set OPENAI_API_KEY environment variable or pass api_key parameter")
    
    def summarize_text(self, text: str, max_length: int = 150) -> str:
        """
        Summarize the given text
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Free tier model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes text clearly and concisely."},
                    {"role": "user", "content": f"Please summarize this text in about {max_length} words:\n\n{text}"}
                ],
                max_tokens=max_length + 50,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def answer_questions(self, text: str, question: str) -> str:
        """
        Answer questions about the given text
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided text. Only use information from the given text."},
                    {"role": "user", "content": f"Text: {text}\n\nQuestion: {question}\n\nPlease answer based only on the information in the text above."}
                ],
                max_tokens=200,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_reading_level(self, text: str) -> str:
        """
        Analyze the reading difficulty level of the text
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in text analysis. Analyze the reading level and provide educational insights."},
                    {"role": "user", "content": f"Analyze the reading level of this text and provide insights about vocabulary complexity, sentence structure, and estimated grade level:\n\n{text}"}
                ],
                max_tokens=300,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_comprehension_questions(self, text: str, num_questions: int = 3) -> List[str]:
        """
        Generate comprehension questions based on the text
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an educational assistant that creates thoughtful comprehension questions about texts."},
                    {"role": "user", "content": f"Create {num_questions} comprehension questions about this text. Make them varied (factual, inferential, analytical):\n\n{text}"}
                ],
                max_tokens=400,
                temperature=0.4
            )
            
            questions_text = response.choices[0].message.content.strip()
            # Simple parsing to extract questions
            questions = [q.strip() for q in questions_text.split('\n') if q.strip() and ('?' in q or q.strip().endswith('?'))]
            return questions[:num_questions]
        except Exception as e:
            return [f"Error generating questions: {str(e)}"]
    
    def explain_difficult_words(self, text: str) -> str:
        """
        Identify and explain difficult words in the text
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful tutor that explains difficult vocabulary in simple terms."},
                    {"role": "user", "content": f"Identify the most difficult or advanced words in this text and provide simple explanations for them:\n\n{text}"}
                ],
                max_tokens=400,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    """
    Demo function to show how to use the Reading AI
    """
    print("=== Reading AI Demo ===")
    print("Note: You need an OpenAI API key to use this fully.")
    print("Get free credits at: https://platform.openai.com/")
    print()
    
    # Initialize the AI
    ai = ReadingAI()
    
    # Sample text for demonstration
    sample_text = """
    Artificial intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving. The ideal characteristic of artificial intelligence is its ability to rationalize and take actions that have the best chance of achieving a specific goal. Machine learning is a subset of artificial intelligence that refers to the ability of machines to receive data and learn for themselves, changing algorithms as they learn more about the information they are processing.
    """
    
    print("Sample text loaded. Choose an option:")
    print("1. Summarize text")
    print("2. Ask a question about the text")
    print("3. Analyze reading level")
    print("4. Generate comprehension questions")
    print("5. Explain difficult words")
    print("6. Use your own text")
    print("0. Exit")
    
    while True:
        choice = input("\nEnter your choice (0-6): ").strip()
        
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
            print("\n--- Reading Level Analysis ---")
            analysis = ai.analyze_reading_level(sample_text)
            print(analysis)
        elif choice == '4':
            print("\n--- Comprehension Questions ---")
            questions = ai.generate_comprehension_questions(sample_text)
            for i, q in enumerate(questions, 1):
                print(f"{i}. {q}")
        elif choice == '5':
            print("\n--- Difficult Words Explained ---")
            explanations = ai.explain_difficult_words(sample_text)
            print(explanations)
        elif choice == '6':
            print("Enter your text (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            sample_text = "\n".join(lines[:-1])  # Remove the last empty line
            print("Text updated! You can now use options 1-5 with your text.")
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()