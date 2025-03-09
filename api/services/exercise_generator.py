import time
import json
import requests
from .knowledge_base import LanguageLearningKB 
from typing import Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential

class ExerciseGenerator:
    def __init__(self, api_key: str, url: str):
        self.api_key = api_key
        self.url = url
        self.knowledge_base = LanguageLearningKB()

    def _create_reading_prompt(self, language: str, level: str, topic: str = None) -> str:
        # Retrieve relevant content
        context = self.knowledge_base.retrieve_relevant_content(language, topic, level)
        
        # Create enhanced prompt with retrieved content
        prompt = f"""Using these examples and rules as reference:
        {json.dumps(context, indent=2)}
        
        Generate a {level} level reading comprehension exercise in {language}
        about {topic if topic else 'general topics'}
        Include:
        1. A passage using appropriate vocabulary and grammar
        2. 5 comprehension questions
        3. Multiple choice answers
        4. Explanations for correct answers
        """
        return prompt

    def generate_reading_exercise(self, language: str, level: str, topic: str = None) -> Dict:
        prompt = self._create_reading_prompt(language, level, topic)
        response = self._call_api(prompt)
        return self._format_reading_exercise(response)

    def generate_grammar_exercise(self, language: str, level: str, grammar_point: str) -> Dict:
        prompt = self._create_grammar_prompt(language, level, grammar_point)
        response = self._call_api(prompt)
        return self._format_grammar_exercise(response)

    def _create_reading_prompt(self, language: str, level: str, topic: str = None) -> str:
        context = self.knowledge_base.retrieve_relevant_content(language, topic, level)
        
        prompt = f"""<s>[INST] You are a language learning expert. Create a {level} level reading comprehension exercise in {language} about {topic if topic else 'general topics'}.

Context and rules:
{json.dumps(context, indent=2)}

The exercise must be returned as a valid JSON object with this structure:
{{
    "title": "Short, relevant title",
    "text": "A passage of 150-200 words using {level} appropriate vocabulary",
    "questions": [
        {{
            "question": "Clear, focused question",
            "options": [
                "A) First option",
                "B) Second option",
                "C) Third option",
                "D) Fourth option"
            ],
            "correct_answer": "A) First option",
            "explanation": "Brief explanation of why this is correct"
        }}
    ]
}}

Create exactly 5 questions with 4 options each. Return only the JSON object, no other text. [/INST]</s>"""
        
        return prompt

    def _create_grammar_prompt(self, language: str, level: str, grammar_point: str) -> str:
        return f"Create a {level} level grammar exercise about {grammar_point} in {language}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_api(self, prompt: str) -> Dict:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 2000,  # Increased token limit
                    "temperature": 0.7,
                    "return_full_text": False,
                    "truncate": False,  # Prevent truncation
                    "max_time": 30  # Maximum generation time
                }
            }
        
            response = requests.post(
                self.url,
                headers=headers,
                json=data,
                timeout=45  # Increased timeout
            )
            
            if response.status_code == 503:
                raise requests.exceptions.RequestException("API is temporarily unavailable (503). Retrying...")
            
            response.raise_for_status()
            
            # Handle potential streaming response
            response_data = response.json()
            if isinstance(response_data, list) and response_data:
                full_text = response_data[0].get("generated_text", "")
                # Ensure we have complete JSON
                if full_text.count('{') != full_text.count('}'):
                    raise ValueError("Incomplete JSON response")
                return {"generated_text": full_text}
            
            raise ValueError("Invalid response format")
        
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")

    def _format_reading_exercise(self, response: Dict) -> Dict:
        try:
            # Clean up the response text
            content = response.get('generated_text', '').replace('----------------------------------------------------------------------------------------------------------------------------------------\n', '')
            
            # Parse the JSON content
            exercise_data = json.loads(content)
            
            return {
                'title': exercise_data.get('title', ''),
                'exercise_type': 'reading',
                'content': exercise_data.get('text', ''),
                'instructions': 'Read the text and answer the questions below.',
                'questions': self._format_questions(exercise_data.get('questions', []))
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            # Fallback to old parsing method if JSON is invalid
            return self._format_reading_exercise_fallback(response)

    def _format_questions(self, questions: List[Dict]) -> List[Dict]:
        formatted_questions = []
        for q in questions:
            # Clean up options (they might be individual strings)
            options = q.get('options', [])
            if isinstance(options, str):
                # Split options if they're in string format
                options = [opt.strip() for opt in options.split('","') if opt.strip()]
            
            formatted_questions.append({
                'question_text': q.get('question', ''),
                'options': options,
                'correct_answer': q.get('correct_answer', ''),
                'explanation': q.get('explanation', '')
            })
        return formatted_questions

    def _format_reading_exercise_fallback(self, response: Dict) -> Dict:
        # Keep the old formatting method as fallback
        content = response.get('generated_text', '')
        # Split into main sections
        sections = content.split('\n\n')
        
        # Extract title and content
        title = next((s.replace('Title: ', '') for s in sections if 'Title:' in s), '')
        text = next((s for s in sections if 'Text:' in s), '')
        questions_section = next((s for s in sections if 'Questions:' in s), '')
        answers_section = next((s for s in sections if 'Answer key:' in s), '')

        
        return {
            'title': title,
            'exercise_type': 'reading',
            'content': text.replace('Text:\n\n', ''),
            'instructions': 'Answer the questions below.',
            'questions': self._parse_questions(questions_section, answers_section)
        }

    def _parse_questions(self, questions_text: str, answers_text: str) -> List[Dict]:
        questions = []
        
        # Split into individual questions and answers
        question_lines = questions_text.replace('Questions:\n\n', '').split('\n')
        answer_lines = answers_text.replace('Answer key:\n\n', '').split('\n')
        
        # Create question-answer pairs
        for q, a in zip(question_lines, answer_lines):
            if q.strip() and a.strip():
                # Remove numbering
                q = q[q.find('.') + 2:] if '.' in q else q
                a = a[a.find('.') + 2:] if '.' in a else a
                
                questions.append({
                    'question_text': q,
                    'options': [],  # You might want to generate options from the answer
                    'correct_answer': a,
                    'explanation': f"The correct answer is: {a}"
                })
        
        return questions

    def _format_grammar_exercise(self, response: Dict) -> Dict:
        content = response.get('generated_text', '')
        sections = content.split('\n\n')
        
        return {
            'title': f'Grammar Exercise',
            'exercise_type': 'grammar',
            'content': sections[0] if sections else '',
            'questions': self._parse_questions(sections[1:])
        }

    def _parse_questions(self, questions_section: str, answers_section: str) -> List[Dict]:
        questions = []
        
        # Clean and split the sections
        question_lines = questions_section.replace('Questions:\n\n', '').split('\n')
        answer_lines = answers_section.replace('Answer key:\n\n', '').split('\n')
        
        # Process each question-answer pair
        for q, a in zip(question_lines, answer_lines):
            if not (q.strip() and a.strip()):
                continue
                
            # Extract question number and text
            q_num, q_text = q.split('. ', 1) if '. ' in q else ('', q)
            a_num, a_text = a.split('. ', 1) if '. ' in a else ('', a)
            
            # Generate plausible wrong options
            options = [a_text]  # Correct answer is first
            wrong_options = self._generate_wrong_options(a_text, questions_section)
            options.extend(wrong_options[:3])  # Add 3 wrong options
            
            # Shuffle options
            import random
            random.shuffle(options)
            
            # Find correct answer index
            correct_index = options.index(a_text)
            
            questions.append({
                'question_text': q_text,
                'options': options,
                'correct_answer': a_text,
                'correct_option_index': correct_index,
                'explanation': f"The correct answer is: {a_text}"
            })
        
        return questions

    def _generate_wrong_options(self, correct_answer: str, context: str) -> List[str]:
        # Extract other answers from context to use as wrong options
        all_answers = [line.split('. ', 1)[1] if '. ' in line else line 
                      for line in context.split('\n') 
                      if line.strip() and line.strip() != correct_answer]
        
        # If we don't have enough wrong options, generate some
        while len(all_answers) < 3:
            all_answers.append(f"Alternative answer {len(all_answers) + 1}")
            
        # Shuffle and return first 3
        import random
        random.shuffle(all_answers)
        return all_answers[:3]

    def _extract_options(self, text: str) -> List[str]:
        # Implement option extraction logic
        pass

    def _extract_answer(self, text: str) -> str:
        # Implement answer extraction logic
        pass

    def _extract_explanation(self, text: str) -> str:
        # Implement explanation extraction logic
        pass