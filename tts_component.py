#!/usr/bin/env python
# coding: utf-8
"""
Streamlit component for text-to-speech functionality in the AI Tutor application.
Provides UI elements for audio playback of explanations and text segments.
"""
import os
import streamlit as st
from typing import Dict, Any, Optional

# Use relative import within the package
from text_to_speech import TextToSpeech

class TTSComponent:
    """
    Streamlit component for handling text-to-speech in the AI Tutor application.
    """
    
    def __init__(self, tts_handler: TextToSpeech):
        """
        Initialize the TTS component.
        
        Args:
            tts_handler: Instance of TextToSpeech to handle audio generation
        """
        self.tts_handler = tts_handler
        
        # Create session state variables if they don't exist
        if 'current_audio_segment_id' not in st.session_state:
            st.session_state.current_audio_segment_id = None # ID of the segment whose audio is loaded
        if 'current_audio_path' not in st.session_state:
            st.session_state.current_audio_path = None # Path to the generated audio file
        if 'audio_generation_error' not in st.session_state:
            st.session_state.audio_generation_error = None

    def render_audio_player_for_segment(self, segment_text: str, segment_id: str, source: Optional[str] = None) -> None:
        """
        Render the audio player specifically for a text segment.
        Generates audio if the segment ID matches the one requested for playback.

        Args:
            segment_text: The text of the segment to potentially play.
            segment_id: A unique identifier for this text segment.
            source: Source of the text (for display purposes).
        """
        # Check if audio needs to be generated for *this* specific segment
        if st.session_state.get('generate_audio_for_segment') == segment_id:
            # Clear the trigger and any previous error/path
            st.session_state.generate_audio_for_segment = None
            st.session_state.current_audio_path = None
            st.session_state.audio_generation_error = None
            st.session_state.current_audio_segment_id = segment_id # Mark this segment as the target

            with st.spinner(f"Generating audio for segment..."):
                result = self.tts_handler.generate_speech_for_explanation(segment_text) # Use existing method
                
                if result["success"]:
                    st.session_state.current_audio_path = result["file_path"]
                    st.success("Audio generated!", icon="🔊")
                else:
                    st.session_state.audio_generation_error = f"Failed to generate audio: {result['error']}"
                    st.error(st.session_state.audio_generation_error)
            
            # Rerun to display the player immediately after generation
            st.experimental_rerun()

        # Display the audio player if the audio for *this* segment is ready
        if st.session_state.current_audio_segment_id == segment_id and st.session_state.current_audio_path:
            audio_path = st.session_state.current_audio_path
            if os.path.exists(audio_path):
                try:
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    # Add a button to clear this specific audio to save space/avoid confusion
                    if st.button("Clear Audio", key=f"clear_audio_{segment_id}"):
                        self._clear_current_audio()
                        st.experimental_rerun()

                except Exception as e:
                    st.error(f"Error loading audio file: {e}")
                    self._clear_current_audio() # Clear state if loading fails
                    st.experimental_rerun()
            else:
                # If file path exists in state but not on disk, clear state
                st.warning("Audio file not found. It might have been cleared.")
                self._clear_current_audio()
                st.experimental_rerun()
        
        # Display error if generation failed for this segment
        elif st.session_state.current_audio_segment_id == segment_id and st.session_state.audio_generation_error:
            st.error(st.session_state.audio_generation_error)
            # Optionally add a retry button or just let the user click play again
            if st.button("Clear Error", key=f"clear_err_{segment_id}"):
                 st.session_state.audio_generation_error = None
                 st.session_state.current_audio_segment_id = None
                 st.experimental_rerun()


    def trigger_audio_generation_for_segment(self, segment_id: str):
        """
        Sets a flag in session state to trigger audio generation for a specific segment 
        on the next rerun.
        """
        # Clear previous audio state before triggering new generation
        self._clear_current_audio()
        st.session_state.generate_audio_for_segment = segment_id
        # No rerun here, the component calling this should handle the rerun

    def _clear_current_audio(self):
        """Clears the current audio state and deletes the associated file."""
        audio_path = st.session_state.get('current_audio_path')
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as e:
                st.warning(f"Could not delete audio file {audio_path}: {e}")
        
        st.session_state.current_audio_segment_id = None
        st.session_state.current_audio_path = None
        st.session_state.audio_generation_error = None
        # Clear the trigger as well if it's still set
        if 'generate_audio_for_segment' in st.session_state:
            st.session_state.generate_audio_for_segment = None

    # --- Keep the explanation-focused method for the Lessons page --- #
    def render_audio_player_for_explanation(self, text: Optional[str] = None, source: Optional[str] = None) -> None:
        """
        Render the audio player for text-to-speech playback of a full explanation.
        This is kept separate for the explanation component.
        Args:
            text: Text to convert to speech (if None, uses current explanation)
            source: Source of the text (for display purposes)
        """
        st.subheader("Listen to Explanation")
        
        # Use a different state key for explanation audio to avoid conflicts with segments
        explanation_audio_key = 'current_explanation_audio'
        explanation_error_key = 'explanation_audio_error'

        # Get text from current explanation if not provided
        if text is None and 'current_explanation' in st.session_state:
            if st.session_state.current_explanation:
                text = st.session_state.current_explanation['text']
                source = st.session_state.current_explanation.get('source', 'explanation')
        
        if not text:
            st.info("No explanation available for text-to-speech.")
            return
        
        # Generate speech button
        if st.button("Generate Explanation Audio"):
            # Clear previous state
            self._clear_explanation_audio()
            with st.spinner("Converting explanation to speech..."):
                result = self.tts_handler.generate_speech_for_explanation(text)
                
                if result["success"]:
                    st.session_state[explanation_audio_key] = result["file_path"]
                    st.success("Explanation audio generated successfully!")
                else:
                    st.session_state[explanation_error_key] = f"Failed to generate audio: {result['error']}"
                    st.error(st.session_state[explanation_error_key])
            st.experimental_rerun()

        # Display audio player if audio is available
        if st.session_state.get(explanation_audio_key):
            audio_path = st.session_state[explanation_audio_key]
            if os.path.exists(audio_path):
                st.write(f"**Audio for:** {source if source else 'Current explanation'}")
                try:
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    if st.button("Clear Explanation Audio"):
                        self._clear_explanation_audio()
                        st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error loading explanation audio file: {e}")
                    self._clear_explanation_audio()
                    st.experimental_rerun()
            else:
                st.warning("Explanation audio file not found.")
                self._clear_explanation_audio()
                st.experimental_rerun()
        elif st.session_state.get(explanation_error_key):
             st.error(st.session_state[explanation_error_key])
             if st.button("Clear Error"):
                 st.session_state[explanation_error_key] = None
                 st.experimental_rerun()

    def _clear_explanation_audio(self):
        """Clears the explanation audio state and deletes the file."""
        explanation_audio_key = 'current_explanation_audio'
        explanation_error_key = 'explanation_audio_error'
        audio_path = st.session_state.get(explanation_audio_key)
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as e:
                st.warning(f"Could not delete explanation audio file {audio_path}: {e}")
        st.session_state[explanation_audio_key] = None
        st.session_state[explanation_error_key] = None
