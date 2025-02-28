from typing import Dict, List
import requests
from .knowledge_base import LanguageLearningKB 
import time
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
        return f"Generate a {level} level reading comprehension exercise in {language}"

    def _create_grammar_prompt(self, language: str, level: str, grammar_point: str) -> str:
        return f"Create a {level} level grammar exercise about {grammar_point} in {language}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_api(self, prompt: str) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1000,
                "temperature": 0.7,
                "return_full_text": False
            }
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=data
        )
        
        if response.status_code == 503:
            # Model is loading
            time.sleep(20)  # Wait for model to load
            response = requests.post(self.base_url, headers=headers, json=data)
        
        response.raise_for_status()
        return {"generated_text": response.json()[0]["generated_text"]}

    def _format_reading_exercise(self, response: Dict) -> Dict:
        # Parse and structure the SmolLM response
        content = response.get('generated_text', '')
        
        # Basic parsing (you'll need to adjust based on actual SmolLM output format)
        sections = content.split('\n\n')
        
        return {
            'title': 'Reading Comprehension Exercise',
            'exercise_type': 'reading',
            'content': sections[0] if sections else '',
            'questions': self._parse_questions(sections[1:])
        }

    def _format_grammar_exercise(self, response: Dict) -> Dict:
        content = response.get('generated_text', '')
        sections = content.split('\n\n')
        
        return {
            'title': f'Grammar Exercise',
            'exercise_type': 'grammar',
            'content': sections[0] if sections else '',
            'questions': self._parse_questions(sections[1:])
        }

    def _parse_questions(self, sections: List[str]) -> List[Dict]:
        questions = []
        for section in sections:
            if 'Question' in section:
                questions.append({
                    'question_text': section,
                    'options': self._extract_options(section),
                    'correct_answer': self._extract_answer(section),
                    'explanation': self._extract_explanation(section)
                })
        return questions

    def _extract_options(self, text: str) -> List[str]:
        # Implement option extraction logic
        pass

    def _extract_answer(self, text: str) -> str:
        # Implement answer extraction logic
        pass

    def _extract_explanation(self, text: str) -> str:
        # Implement explanation extraction logic
        pass