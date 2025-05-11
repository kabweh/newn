"""
Streamlit component for lesson explanation in the AI Tutor application.
Provides UI elements for explaining uploaded content and integrates TTS.
"""
import streamlit as st
from typing import Dict, Any, Optional

# Use relative import within the package
from lesson_explainer import LessonExplainer
# Assuming tts_component is initialized in streamlit_app.py and available in session_state

class ExplanationComponent:
    """
    Streamlit component for handling lesson explanations in the AI Tutor application.
    """
    
    def __init__(self, lesson_explainer: LessonExplainer):
        """
        Initialize the explanation component.
        
        Args:
            lesson_explainer: Instance of LessonExplainer to generate explanations
        """
        self.lesson_explainer = lesson_explainer
        
        # Create session state variables if they don't exist
        if 'content_to_explain' not in st.session_state:
            st.session_state.content_to_explain = None
        
        if 'current_explanation' not in st.session_state:
            st.session_state.current_explanation = None
        
        if 'explanation_history' not in st.session_state:
            st.session_state.explanation_history = []
    
    def render_explanation_section(self) -> None:
        """
        Render the explanation section in the Streamlit UI, including TTS.
        """
        st.header("Lesson Explanations")
        
        # Show explanation options
        complexity_level = st.radio(
            "Explanation complexity:",
            options=["simple", "medium", "advanced"],
            index=1,  # Default to medium
            horizontal=True,
            help="Choose the level of detail for the explanation. 'Medium' provides a teacher-like explanation."
        )
        
        # Check if there's content to explain from upload component
        if st.session_state.content_to_explain:
            with st.expander("Content to explain", expanded=True):
                source_filename = st.session_state.content_to_explain.get('source', 'Unknown Source')
                st.write(f"**Source:** {source_filename}")
                st.text_area(
                    "Content",
                    value=st.session_state.content_to_explain['text'],
                    height=200,
                    disabled=True
                )
            
            # Generate explanation button
            if st.button("Generate Explanation"):
                with st.spinner("Generating explanation..."):
                    # Pass source filename for better subject identification
                    explanation = self.lesson_explainer.generate_explanation(
                        st.session_state.content_to_explain['text'],
                        complexity_level,
                        source_filename=source_filename 
                    )
                    
                    # Store in session state
                    st.session_state.current_explanation = {
                        'text': explanation,
                        'source': source_filename,
                        'complexity': complexity_level
                    }
                    
                    # Add to history
                    st.session_state.explanation_history.append(st.session_state.current_explanation)
                    
                    # Clear content to explain and any previous audio
                    st.session_state.content_to_explain = None
                    if 'current_audio' in st.session_state:
                         st.session_state.current_audio = None # Clear old audio when new explanation is generated
                    
                    # Rerun to update UI
                    st.experimental_rerun()
        
        # Display current explanation if available
        if st.session_state.current_explanation:
            st.subheader("Explanation")
            st.info(f"Explaining content from: {st.session_state.current_explanation['source']} (Complexity: {st.session_state.current_explanation['complexity']})")
            st.write(st.session_state.current_explanation['text'])
            
            st.markdown("---") # Separator before TTS
            
            # --- Integrate TTS Component --- #
            # Check if the TTS component is available in session state (initialized in streamlit_app.py)
            if 'tts_component' in st.session_state:
                # Call the TTS component's render method, passing the current explanation text and source
                st.session_state.tts_component.render_audio_player(
                    text=st.session_state.current_explanation['text'], 
                    source=st.session_state.current_explanation['source']
                )
            else:
                st.warning("TTS component not initialized.")
    
    def render_explanation_history(self) -> None:
        """
        Render the history of generated explanations.
        """
        if not st.session_state.explanation_history:
            return
        
        st.header("Explanation History")
        
        # Display history in chronological order (newest first)
        for idx, explanation in enumerate(reversed(st.session_state.explanation_history)):
            # Use a unique key based on index and source/complexity to avoid conflicts
            expander_key = f"history_{idx}_{explanation['source']}_{explanation['complexity']}"
            button_key = f"view_again_{idx}_{explanation['source']}_{explanation['complexity']}"
            
            with st.expander(f"Explanation for {explanation['source']} ({explanation['complexity']})", key=expander_key):
                st.write(explanation['text'])
                
                # Button to set as current explanation
                if st.button(f"View & Listen Again", key=button_key):
                    st.session_state.current_explanation = explanation
                    # Clear any existing audio when viewing history item again
                    if 'current_audio' in st.session_state:
                         st.session_state.current_audio = None
                    st.experimental_rerun()
    
    # This method might not be needed if triggering is done via button in upload_component
    # def explain_content(self, text: str, source: str, complexity_level: str = "medium") -> None:
    #     """
    #     Set content to be explained.
        
    #     Args:
    #         text: Text content to explain
    #         source: Source of the content (e.g., filename)
    #         complexity_level: Desired complexity level
    #     """
    #     st.session_state.content_to_explain = {
    #         'text': text,
    #         'source': source
    #     }
    
    def get_current_explanation(self) -> Optional[Dict[str, Any]]:
        """
        Get the current explanation from session state.
        
        Returns:
            Dictionary containing explanation information or None
        """
        return st.session_state.current_explanation
