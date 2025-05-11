#!/usr/bin/env python
# coding: utf-8
import re
from typing import Dict, Any, List, Optional
import random # Added for simulating variability

class LessonExplainer:
    """
    Generates explanations for educational content in a conversational, teacher-like style,
    attempting to base explanations more directly on the provided text content.
    """

    def __init__(self):
        """Initialize the lesson explainer."""
        # Define a maximum character limit to avoid overly long explanations for very large documents
        self.MAX_TEXT_CHARS_FOR_EXPLANATION = 15000 # Increased limit slightly (~2500 words)
        pass

    def generate_explanation(self, text: str, complexity_level: str = "medium", source_filename: Optional[str] = None) -> str:
        """
        Generate a conversational, teacher-like explanation for the given text.
        Considers the full text up to a reasonable limit and tries to base explanation on it.

        Args:
            text: The text content to explain.
            complexity_level: Desired complexity level (simple, medium, advanced).
            source_filename: The name of the source file (optional, for context).

        Returns:
            Conversational explanation of the content.
        """
        # Remove excessive whitespace and normalize text
        processed_text = self._preprocess_text(text)

        if not processed_text.strip():
            return "I don\t see any content to explain. Please upload some material first."

        # Limit text length to prevent excessive processing time / cost
        original_length = len(processed_text)
        if original_length > self.MAX_TEXT_CHARS_FOR_EXPLANATION:
            processed_text = processed_text[:self.MAX_TEXT_CHARS_FOR_EXPLANATION]
            warning = f"(Note: The explanation is based on the first {self.MAX_TEXT_CHARS_FOR_EXPLANATION:,} characters of the document due to its length of {original_length:,} characters.)\n\n"
        else:
            warning = ""

        # Identify the subject matter
        subject = self._identify_subject(processed_text, source_filename)

        # Generate explanation based on complexity level
        # Focus on enhancing the medium level significantly
        if complexity_level == "simple":
            explanation = self._generate_simple_explanation(processed_text, subject)
        elif complexity_level == "advanced":
            explanation = self._generate_advanced_explanation(processed_text, subject)
        else:  # medium (default)
            explanation = self._generate_teacher_explanation(processed_text, subject)

        return warning + explanation

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text by removing excessive whitespace and normalizing.

        Args:
            text: Raw text to preprocess.

        Returns:
            Preprocessed text.
        """
        # Replace multiple newlines with a single newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Replace multiple spaces with a single space
        text = re.sub(r" {2,}", " ", text)
        # Attempt to fix common OCR issues like ligatures or misinterpretations
        text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
        # Remove page numbers or headers/footers if possible (simple example)
        text = re.sub(r"^\s*Page \d+\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*Chapter \d+\s*$", "", text, flags=re.MULTILINE)
        # Remove lines that seem like just noise (e.g., single characters, short fragments)
        lines = text.split("\n")
        cleaned_lines = [line for line in lines if len(line.strip()) > 5 or line.strip() == ""]
        text = "\n".join(cleaned_lines)

        return text.strip()

    def _identify_subject(self, text: str, source_filename: Optional[str] = None) -> str:
        """
        Attempt to identify the subject matter of the text, using filename as a hint.

        Args:
            text: The text content to analyze.
            source_filename: The name of the source file (optional).

        Returns:
            Identified subject or "general" if unclear.
        """
        text_lower = text.lower()
        filename_lower = source_filename.lower() if source_filename else ""

        # Prioritize filename hints
        if "ratio" in filename_lower or "math" in filename_lower or "algebra" in filename_lower or "geometry" in filename_lower:
            return "mathematics"
        if "history" in filename_lower:
            return "history"
        if "science" in filename_lower or "biology" in filename_lower or "chemistry" in filename_lower or "physics" in filename_lower:
            return "science"
        if "literature" in filename_lower or "novel" in filename_lower or "poem" in filename_lower:
            return "literature"
        if "language" in filename_lower or "grammar" in filename_lower or "vocabulary" in filename_lower:
            return "language"

        # Fallback to text content analysis - expanded keywords
        if any(term in text_lower for term in ["ratio", "equation", "formula", "calculation", "algebra", "geometry", "solve for x", "fraction", "decimal", "percent", "theorem", "proof", "variable", "constant", "graph", "function"]):
            return "mathematics"
        if any(term in text_lower for term in ["history", "century", "war", "civilization", "ancient", "revolution", "president", "king", "queen", "empire", "dynasty", "treaty", "primary source", "secondary source"]):
            return "history"
        if any(term in text_lower for term in ["science", "biology", "chemistry", "physics", "experiment", "molecule", "atom", "cell", "energy", "force", "hypothesis", "theory", "observation", "result", "method", "organism", "ecosystem"]):
            return "science"
        if any(term in text_lower for term in ["literature", "novel", "poem", "author", "character", "story", "theme", "metaphor", "symbolism", "narrative", "plot", "setting", "protagonist", "antagonist"]):
            return "literature"
        if any(term in text_lower for term in ["grammar", "vocabulary", "language", "verb", "noun", "adjective", "sentence", "paragraph", "syntax", "semantics", "phonetics", "linguistics"]):
            return "language"

        return "general"

    def _generate_teacher_explanation(self, text: str, subject: str) -> str:
        """
        Generate a detailed, teacher-like explanation with examples based on the full text (up to limit).
        Simulates a better explanation by extracting key sentences/paragraphs.

        Args:
            text: The text content to explain.
            subject: Identified subject matter.

        Returns:
            Teacher-like explanation.
        """
        # --- This is still a placeholder for a more sophisticated LLM call --- #
        # The logic below simulates a better explanation based on more text
        # but a real LLM would provide much better quality and coherence.

        intro = f"Okay class, let's take a closer look at this material on {subject}. It seems quite interesting! I'll guide you through the main points from the text provided. Pay attention, and feel free to ask questions if anything isn't clear.\n\n"
        body = ""
        examples = ""
        summary = ""
        outro = "\n\nAlright, that covers the main topics discussed in the text we looked at. I hope breaking it down like this helps you grasp the concepts better. Remember, reviewing and practicing is key! Let me know if you need further clarification on any part."

        # Simulate extracting key points/paragraphs from the *entire* text (up to the limit)
        # Split into potential paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50] # Consider paragraphs > 50 chars
        
        # If few paragraphs, split by sentences
        if len(paragraphs) < 3:
            sentences = re.split(r"[.!?]+\s+", text) # Split by sentence endings
            key_items = [s.strip() for s in sentences if len(s.strip()) > 30] # Consider sentences > 30 chars
            item_type = "sentence"
        else:
            key_items = paragraphs
            item_type = "paragraph"

        num_items_to_discuss = min(len(key_items), 5) # Discuss up to 5 key items
        
        if num_items_to_discuss == 0:
             body = "Hmm, I couldn't seem to extract distinct points from the text to discuss in detail. It might be formatted unusually. However, the overall topic seems to be about {subject}.\n"
        else:
             body = f"Let's focus on some key parts from the text. I've picked out {num_items_to_discuss} important {'paragraphs' if item_type == 'paragraph' else 'sentences'} to discuss:\n\n"
             # Select a few items randomly or sequentially to discuss
             indices_to_discuss = random.sample(range(len(key_items)), k=num_items_to_discuss) if len(key_items) > num_items_to_discuss else range(num_items_to_discuss)
             
             for i, index in enumerate(indices_to_discuss):
                 item = key_items[index]
                 # Simulate generating an explanation for this item
                 body += f"**Point {i+1} (from the text):** \"{item[:150]}{'...' if len(item) > 150 else ''}\"\n"
                 body += f"*What this means:* This {item_type} seems to be explaining [your interpretation/summary of the item's main idea, e.g., the definition of a ratio, a specific historical event, a scientific process]. It connects to the overall topic by [explain connection].\n\n"

        # Add subject-specific examples/summary if possible, trying to relate to extracted items
        if subject == "mathematics":
            if "ratio" in text.lower():
                examples = ("\n\n**Example related to Ratios (from the text concepts):** The text mentions comparing quantities, like cats to dogs or red to blue marbles. Let's apply this. If a class has 12 girls and 18 boys:\n" 
                            "- The ratio of girls to boys is 12:18. We can simplify this by dividing both by 6, giving us 2:3. For every 2 girls, there are 3 boys.\n" 
                            "- The ratio of boys to the *total* students (12+18=30) is 18:30. Simplifying by dividing by 6 gives 3:5. 3 out of every 5 students are boys.")
                summary = "\n\n**Key Takeaways on Ratios (based on text):**\n1. Ratios compare two numbers or quantities.\n2. The order in a ratio is important (e.g., girls to boys is different from boys to girls).\n3. Ratios can be written with 'to', a colon (:), or as a fraction.\n4. Simplify ratios like fractions to make them easier to understand."
            else:
                examples = "\n\nFor instance, if the text discussed solving equations like 2x + 3 = 11, we'd use inverse operations..."
                summary = "\n\nRemember the key steps for this type of math problem discussed in the text: [Summarize steps/concepts based on extracted items]."

        elif subject == "history":
            examples = "\n\nFor example, if the text mentioned the causes of a war, think about how those factors (like disagreements over land or resources) led to the conflict..."
            summary = "\n\nMain points about this historical topic from the text are: [Summarize key events/causes/effects based on extracted items]."

        elif subject == "science":
            examples = "\n\nFor example, if the text described an experiment, consider the hypothesis (what they expected to happen), the method (what they did), and the results (what they found)..."
            summary = "\n\nKey scientific ideas from the text include: [Summarize concepts/processes based on extracted items]."

        else: # General subject
            examples = "\n\nWe can relate the ideas in the text to everyday life. For example..."
            summary = "\n\nIn short, the text seems to emphasize: [Summarize based on extracted items]."

        # Combine parts
        explanation = intro + body + examples + summary + outro
        return explanation

    # --- Simple and Advanced explanations remain less detailed placeholders --- #
    def _generate_simple_explanation(self, text: str, subject: str) -> str:
        """
        Generate a simple explanation suitable for younger students.
        (Placeholder - less detailed than teacher explanation)
        """
        # Process a smaller portion for simple explanation
        sentences = re.split(r"[.!?]+\s+", text)
        first_sentence = sentences[0].strip() if sentences else ""
        explanation = f"Hi there! Let's look at this {subject} topic. The first sentence says: '{first_sentence}'. It's basically saying that... [Simplified summary]. For example, think about... [Simple analogy]. Does that help a bit?"
        return explanation

    def _generate_advanced_explanation(self, text: str, subject: str) -> str:
        """
        Generate an advanced explanation for older or advanced students.
        (Placeholder - more formal than teacher explanation)
        """
        # Process more text for advanced explanation
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
        key_concepts = []
        num_concepts = min(len(paragraphs), 3)
        if num_concepts > 0:
             indices = random.sample(range(len(paragraphs)), k=num_concepts) if len(paragraphs) > num_concepts else range(num_concepts)
             for i, index in enumerate(indices):
                 para = paragraphs[index]
                 key_concepts.append(f"[Inferred Key Concept {i+1} from paragraph starting '{para[:50]}...']" )
        else:
             key_concepts = ["[Could not extract distinct concepts]"] * 3

        explanation = f"Analyzing this text on {subject}, we can discern several key principles. Firstly, the concept of {key_concepts[0]} is introduced... This relates to {key_concepts[1]}... Furthermore, {key_concepts[2]}... A critical perspective might consider... In essence, the material argues that... Would you like a deeper dive into any specific aspect?"
        return explanation
