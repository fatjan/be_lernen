from typing import List, Dict
import json
import os

class LanguageLearningKB:
    def __init__(self):
        self.rules = {
            'German': {
                'A1': {
                    'grammar': [
                        'Simple present tense',
                        'Basic word order',
                        'Personal pronouns',
                        'Regular verbs'
                    ],
                    'vocabulary': [
                        'Basic greetings',
                        'Numbers',
                        'Days and months',
                        'Common nouns'
                    ]
                },
                'A2': {
                    'grammar': [
                        'Advanced present tense',
                        'Complex word order',
                        'Conditional sentences',
                        'Irregular verbs'
                    ],
                    'vocabulary': [
                        'More complex greetings',
                        'Quantifiers',
                        'Time expressions',
                        'Frequent nouns'
                    ]
                },
                'B1': {
                    'grammar': [
                        'Passive voice',
                        'Prepositions',
                        'Adjectives',
                        'Adverbs'
                    ],
                    'vocabulary': [
                        'More complex vocabulary',
                        'Quantifiers',
                        'Time expressions',
                        'Frequent nouns'
                    ]
                },
                'B2': {
                    'grammar': [
                        'Imperative mood',
                        'Interrogative sentences',
                        'Relative clauses',
                        'Conjunctions'
                    ],
                    'vocabulary': [
                        'More complex vocabulary',
                        'Quantifiers',
                        'Time expressions',
                        'Frequent nouns'
                    ]
                }
            },
            'English': {
                'A1': {
                    'grammar': [
                        'Simple present tense',
                        'Basic word order',
                        'Personal pronouns',
                        'Regular verbs'
                    ],
                    'vocabulary': [
                        'Basic greetings',
                        'Numbers',
                        'Days and months',
                        'Common nouns'
                    ]
                },
                'A2': {
                    'grammar': [
                        'Advanced present tense',
                        'Complex word order',
                        'Conditional sentences',
                        'Irregular verbs'
                    ],
                    'vocabulary': [
                        'More complex greetings',
                        'Quantifiers',
                        'Time expressions',
                        'Frequent nouns'
                    ]
                },
                'B1': {
                    'grammar': [
                        'Passive voice',
                        'Prepositions',
                        'Adjectives',
                        'Adverbs'
                    ],
                    'vocabulary': [
                        'More complex vocabulary',
                        'Quantifiers',
                        'Time expressions',
                        'Frequent nouns'
                    ]
                },
                'B2': {
                    'grammar': [
                        'Imperative mood',
                        'Interrogative sentences',
                        'Relative clauses',
                        'Conjunctions'
                    ],
                    'vocabulary': [
                        'More complex vocabulary',
                        'Quantifiers',
                        'Time expressions',
                        'Frequent nouns'
                    ]
                }
            }
        }

    def retrieve_relevant_content(self, language: str, topic: str = None, level: str = None) -> dict:
        """Retrieve relevant content based on language, topic, and level."""
        language_rules = self.rules.get(language, {})
        level_rules = language_rules.get(level, {})
        
        context = {
            "language": language,
            "level": level,
            "topic": topic,
            "grammar_rules": level_rules.get('grammar', []),
            "vocabulary_scope": level_rules.get('vocabulary', [])
        }
        
        return context

    def _find_relevant_rules(self, language: str, topic: str = None, level: str = None) -> list:
        """Find relevant rules based on language, topic, and level."""
        language_rules = self.rules.get(language, {})
        level_rules = language_rules.get(level, {})
        
        relevant_rules = []
        if topic:
            # Add topic-specific rules if available
            topic_rules = level_rules.get('topics', {}).get(topic, [])
            relevant_rules.extend(topic_rules)
        
        # Add general rules for the level
        relevant_rules.extend(level_rules.get('grammar', []))
        
        return relevant_rules