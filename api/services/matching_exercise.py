import random
from typing import List, Dict

class MatchingExerciseGenerator:
    @staticmethod
    def generate(user_words: List[Dict], num_pairs: int = 10) -> Dict:
        """Generate a matching exercise from user's words."""
        # Select random words if we have more than num_pairs
        selected_words = random.sample(user_words, min(len(user_words), num_pairs))
        
        # Create shuffled translations
        words = [w['word'] for w in selected_words]
        translations = [w['translation'] for w in selected_words]
        shuffled_translations = translations.copy()
        random.shuffle(shuffled_translations)
        
        return {
            'exercise_type': 'matching',
            'title': 'Match the words with their translations',
            'instructions': 'Match each word with its correct translation',
            'words': words,
            'translations': shuffled_translations,
            'correct_pairs': dict(zip(words, translations))
        }