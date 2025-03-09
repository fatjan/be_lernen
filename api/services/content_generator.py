import json
import requests
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from .knowledge_base import LanguageLearningKB

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, api_key: str, url: str):
        self.api_key = api_key
        self.url = url
        self.knowledge_base = LanguageLearningKB() 

    def generate_reading_content(self, language: str, level: str, topic: str = None) -> dict:
        prompt = self._create_reading_prompt(language, level, topic)
        try:
            response = self._call_api(prompt)
            if isinstance(response, list) and response:
                content = response[0].get('generated_text', '')
                # Extract the actual content
                if '[/INST]' in content:
                    content = content.split('[/INST]')[1].strip()
                
                # Extract title, content and topic
                title_match = content.split('Title: ')[-1].split('\n')[0].strip('"')
                content_match = content.split('Content:\n```\n')[1].split('\n\nTopic:')[0].strip()
                topic_match = content.split('Topic: ')[-1].strip("'}")
                
                return {
                    'title': title_match,
                    'content': content_match,
                    'topic': topic_match,
                    'language': language,
                    'level': level
                }
            raise ValueError("Invalid response format from API")
        except Exception as e:
            logger.error(f"Content generation error: {str(e)}, Raw response: {response}")
            raise ValueError(f"Failed to generate content: {str(e)}")

    def _create_reading_prompt(self, language: str, level: str, topic: str = None) -> str:
        context = self.knowledge_base.retrieve_relevant_content(language, topic, level)
        
        prompt = f"""<s>[INST] You are a language learning content creator. Create a {level} level reading passage in {language} about {topic if topic else 'general topics'}.

Context and rules:
{json.dumps(context, indent=2)}

Return a JSON object with this structure:
{{
    "title": "Short, engaging title",
    "content": "A passage of 150-200 words using {level} appropriate vocabulary and grammar",
    "topic": "Main topic of the text"
}}

Make sure the content is:
- Appropriate for {level} level
- Culturally relevant
- Engaging and educational
- Natural and fluent {language}

Return only the JSON object, no other text. [/INST]</s>"""
        return prompt

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_api(self, prompt: str) -> dict:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(
                self.url,
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 1000,
                        "temperature": 0.7
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")

    def _format_response(self, response: dict) -> dict:
        try:
            content = response[0]["generated_text"]
            return json.loads(content)
        except Exception as e:
            raise Exception(f"Failed to parse response: {str(e)}")