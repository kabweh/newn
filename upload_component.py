#!/usr/bin/env python
# coding: utf-8
"""
Streamlit component for file upload functionality in the AI Tutor application.
Provides UI elements for uploading, displaying files, and an interactive reader
with improved text segmentation for audio playback.
"""
import os
import streamlit as st
from typing import Dict, Any, List
import re

# Use relative import within the package
from upload_manager import UploadManager
# Assuming tts_component is initialized in streamlit_app.py and available in session_state

class UploadComponent:
    """
    Streamlit component for handling file uploads and interactive reading.
    """
    
    def __init__(self, upload_manager: UploadManager):
        """
        Initialize the upload component.
        
        Args:
            upload_manager: Instance of UploadManager to handle file processing
        """
        self.upload_manager = upload_manager
        
        # Create session state variables if they don't exist
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
        # Ensure TTS component state exists (might be redundant if initialized elsewhere)
        if 'tts_component' not in st.session_state:
             # This is a fallback, ideally it's initialized in the main app
             st.warning("TTS component not found in session state during UploadComponent init.")
             st.session_state.tts_component = None 

    def _segment_text(self, text: str, min_length: int = 150) -> List[str]:
        """
        Segments text into meaningful chunks suitable for audio playback.
        Splits by double newlines and merges short consecutive segments.

        Args:
            text: The text to segment.
            min_length: The approximate minimum character length for a segment.

        Returns:
            A list of text segments.
        """
        # Split by double newlines or more, preserving structure better
        raw_segments = re.split(r'(\n\s*){2,}', text)
        
        merged_segments = []
        current_segment = ""

        for seg in raw_segments:
            if seg is None: continue # Skip separators captured by regex groups
            
            cleaned_seg = seg.strip()
            if not cleaned_seg: # Skip empty lines or whitespace-only lines
                continue

            # Replace single newlines within a segment with spaces
            cleaned_seg = re.sub(r'\s*\n\s*', ' ', cleaned_seg)

            # If current_segment is empty, start with the new cleaned segment
            if not current_segment:
                current_segment = cleaned_seg
            # If current_segment is too short, append the new one
            elif len(current_segment) < min_length:
                current_segment += " " + cleaned_seg
            # If current_segment is long enough, finalize it and start new segment
            else:
                merged_segments.append(current_segment)
                current_segment = cleaned_seg

        # Add the last accumulated segment if it exists
        if current_segment:
            merged_segments.append(current_segment)
            
        # Final check: if any segment is excessively long, try splitting by sentences? (Future enhancement)
        # For now, return the merged segments
        return merged_segments

    def render_upload_section(self) -> None:
        """
        Render the file upload section in the Streamlit UI.
        """
        st.header("Upload Learning Materials")
        
        # File uploader widget
        st.write("Upload Images (JPG/PNG), PDF, or DOCX files:")
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["jpg", "jpeg", "png", "pdf", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        # Process uploaded files when the upload button is clicked
        if uploaded_files and st.button("Process Uploads"):
            with st.spinner("Processing files..."):
                newly_processed_files = []
                for uploaded_file in uploaded_files:
                    # Skip if file was already processed in this session
                    if any(f.get('original_filename') == uploaded_file.name for f in st.session_state.uploaded_files):
                        st.info(f"Skipping already processed file: {uploaded_file.name}")
                        continue
                    
                    # Process the file
                    file_info = self.upload_manager.process_upload(uploaded_file, uploaded_file.name)
                    
                    # Add to session state if successful
                    if file_info and file_info.get("success"):
                        newly_processed_files.append(file_info)
                        st.success(f"Successfully processed: {uploaded_file.name}")
                    elif file_info:
                        # If text extraction failed, the 'error' might be in the text field
                        error_msg = file_info.get('extracted_text') if isinstance(file_info.get('extracted_text'), str) and "Error" in file_info.get('extracted_text') else file_info.get('error', 'Unknown error')
                        st.error(f"Failed to process {uploaded_file.name}: {error_msg}")
                        # Still add file info so user sees the error message
                        if not file_info.get("success"): # Ensure success is False
                             file_info["success"] = False
                        newly_processed_files.append(file_info)
                    else:
                         st.error(f"Failed to process {uploaded_file.name}: Processing returned no information.")

                # Prepend newly processed files to the list so they appear first
                st.session_state.uploaded_files = newly_processed_files + st.session_state.uploaded_files
                # Rerun to update the display immediately
                st.experimental_rerun()

    def render_uploaded_files(self) -> None:
        """
        Render the list of uploaded files with options to view content and interactive reader.
        Uses improved text segmentation.
        """
        if not st.session_state.uploaded_files:
            st.info("No files have been uploaded yet.")
            return
        
        st.header("Uploaded Materials")
        
        files_to_remove_indices = []

        for idx, file_info in enumerate(st.session_state.uploaded_files):
            # Defensive check for file_info dictionary
            if not isinstance(file_info, dict):
                st.warning(f"Skipping invalid file entry at index {idx}.")
                continue

            # Ensure a unique and valid key for the expander using .get() with defaults
            saved_fn = file_info.get('saved_filename', f'missing_fn_{idx}')
            original_fn = file_info.get('original_filename', f'Unknown File {idx}')
            file_type_upper = file_info.get('file_type', 'unknown').upper()
            
            expander_label = f"{original_fn} ({file_type_upper})"

            try:
                # Removed key= argument for compatibility
                with st.expander(expander_label):
                    # Display file information
                    st.write(f"**File Type:** {file_type_upper}")
                    
                    # Display file preview based on type
                    file_path = file_info.get('file_path')
                    if file_info.get('file_type') == 'image' and file_path:
                        st.image(file_path, caption=original_fn)
                    
                    # Display extracted text if available and successful
                    extracted_text = file_info.get('extracted_text')
                    is_extraction_error = isinstance(extracted_text, str) and ("Error" in extracted_text or "failed" in extracted_text.lower() or "not found" in extracted_text.lower())
                    
                    if extracted_text and not is_extraction_error:
                        st.subheader("Extracted Text (Full)")
                        st.text_area("Full Content", value=extracted_text, height=200, key=f"full_text_{idx}_{saved_fn}")
                        
                        # --- Interactive Reader Section --- #
                        st.subheader("Interactive Reader")
                        st.caption("Click the 🔊 button next to a paragraph to hear it read aloud.")

                        # Use the improved segmentation method
                        segments = self._segment_text(extracted_text)

                        tts_component = st.session_state.get('tts_component')
                        currently_playing_segment_id = st.session_state.get('current_audio_segment_id')

                        if not tts_component:
                            st.warning("TTS is not available.")
                        else:
                            if not segments:
                                st.info("Could not segment text for interactive reading.")
                            else:
                                for seg_idx, segment_text in enumerate(segments):
                                    if not segment_text: continue # Should be handled by _segment_text, but double-check
                                    
                                    segment_id = f"{saved_fn}_seg_{seg_idx}"
                                    
                                    # Display segment with potential highlighting
                                    is_playing = (currently_playing_segment_id == segment_id)
                                    if is_playing:
                                        # Use markdown for highlighting (simple background color)
                                        st.markdown(f"<div style='background-color: #ffff99; padding: 5px; border-radius: 3px;'>{segment_text}</div>", unsafe_allow_html=True)
                                    else:
                                        st.write(segment_text)

                                    # Add Play button and render audio player placeholder
                                    button_col, player_col = st.columns([1, 5])
                                    with button_col:
                                        play_button_key = f"play_{segment_id}"
                                        if st.button(f"🔊 Play", key=play_button_key, help="Read this paragraph aloud"):
                                            tts_component.trigger_audio_generation_for_segment(segment_id)
                                            st.experimental_rerun()
                                    
                                    with player_col:
                                        # This will display the player if audio for this segment is ready
                                        tts_component.render_audio_player_for_segment(segment_text, segment_id, source=f"Paragraph {seg_idx+1}")
                                    
                                    st.markdown("----") # Separator between segments

                        # --- End Interactive Reader Section --- #

                        # Add "Explain" button for this content (navigates to Lessons page)
                        explain_button_key = f"explain_{idx}_{saved_fn}"
                        if st.button(f"Explain this content", key=explain_button_key):
                            st.session_state.content_to_explain = {
                                'text': extracted_text, # Use the full extracted text
                                'source': original_fn
                            }
                            # Set navigation flag or callback if needed to switch page
                            st.session_state.navigate_to = 'Lessons'
                            st.experimental_rerun() 
                    
                    # Handle cases where text extraction failed or yielded no text
                    elif is_extraction_error:
                         st.error(f"Text Extraction Failed: {extracted_text}")
                    elif file_info.get('file_type') != 'image': # Don't show 'no text' for images unless OCR failed
                        st.warning("No text could be extracted from this file.")
                    
                    st.markdown("----")
                    # Option to remove file
                    remove_button_key = f"remove_{idx}_{saved_fn}"
                    if st.button(f"Remove File", key=remove_button_key):
                        files_to_remove_indices.append(idx)
                        # Defer actual removal and rerun until after the loop
            except Exception as e:
                 # Catch errors within the expander, provide more context
                 st.error(f"Error displaying file '{original_fn}' (Index: {idx}, Saved: {saved_fn}): {e}") 

        # Process removals after iterating
        if files_to_remove_indices:
            # Remove files from session state in reverse index order to avoid shifting issues
            for index in sorted(files_to_remove_indices, reverse=True):
                removed_file = st.session_state.uploaded_files.pop(index)
                # Optionally, remove the actual file from disk
                try:
                    if removed_file and removed_file.get('file_path') and os.path.exists(removed_file['file_path']):
                        os.remove(removed_file['file_path'])
                        # Also try removing associated audio files if naming convention allows
                        # (This part is complex without a clear audio file naming strategy)
                except OSError as e:
                    st.warning(f"Could not remove file from disk: {e}")
            
            # Clear any audio state related to the removed file (difficult without tracking)
            # For simplicity, just clear the current audio state
            if 'tts_component' in st.session_state and hasattr(st.session_state.tts_component, '_clear_current_audio'):
                 st.session_state.tts_component._clear_current_audio()
            if 'tts_component' in st.session_state and hasattr(st.session_state.tts_component, '_clear_explanation_audio'):
                 st.session_state.tts_component._clear_explanation_audio()

            st.experimental_rerun()

    
    def get_uploaded_files(self) -> List[Dict[str, Any]]:
        """
        Get the list of uploaded files from session state.
        
        Returns:
            List of dictionaries containing file information
        """
        return st.session_state.uploaded_files
