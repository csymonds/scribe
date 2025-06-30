# This file allows the user to transcribe any media file supported by pydub to a .txt file using the openAI Whisper API.
# the user can specify the path to the media file and the path to the output text file.

#imports
import shutil
import os
import utils
import threading
from pydub import AudioSegment
import tkinter as tk
from tkinter import filedialog
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# global variables
video_paths = ""
working = False
pending_messages = []  # Thread-safe message queue for GUI updates

def process_audio(video_path):
    """Process audio file into chunks, with comprehensive error handling"""
    try:
        # Validate file exists and basic checks
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"File not found: {video_path}")
        
        # Check file size (warn if very large)
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb > 500:  # 500MB threshold
            logger.warning(f"Large file detected: {file_size_mb:.2f} MB. This may cause memory issues.")
        
        # Get file info using os.path for better reliability
        video_dir_path = os.path.dirname(video_path)
        video_filename = os.path.basename(video_path)
        video_name, video_ext = os.path.splitext(video_filename)
        
        logger.info(f"Processing: {video_filename} ({file_size_mb:.2f} MB)")
        
        # Create unique directory name
        video_chunk_base_name = video_name.replace(" ", "_") + "_chunks"
        tmp_output_dir = os.path.join(video_dir_path, video_chunk_base_name)
        
        logger.info(f"Creating directory: {video_chunk_base_name}")
        logger.info(f"Video path: {video_dir_path}")
        logger.info(f"Output directory: {tmp_output_dir}")
        
        # Create directory if it doesn't exist
        os.makedirs(tmp_output_dir, exist_ok=True)
        
        # Load and process audio file
        logger.info(f"Loading audio file: {video_path}")
        logger.info(f"File size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
        
        try:
            # Try to load with explicit format first
            file_ext = video_ext.lower().lstrip('.')
            logger.info(f"Attempting to load as format: {file_ext}")
            
            if file_ext in ['mp4', 'mov', 'avi']:
                # For video files, be more explicit about format
                input_file = AudioSegment.from_file(video_path, format=file_ext)
            else:
                # For audio files, let pydub auto-detect
                input_file = AudioSegment.from_file(video_path)
                
        except Exception as e:
            logger.error(f"Failed to load with format '{file_ext}': {str(e)}")
            logger.info("Attempting to load with auto-detection...")
            try:
                # Fallback: let pydub auto-detect
                input_file = AudioSegment.from_file(video_path)
            except Exception as e2:
                logger.error(f"Failed to load with auto-detection: {str(e2)}")
                raise ValueError(f"Could not load audio file {video_path}. File may be corrupted or in unsupported format.")
        
        duration_in_milliseconds = len(input_file)
        logger.info(f"Successfully loaded audio. Duration: {duration_in_milliseconds / 1000:.2f} seconds")
        
        if duration_in_milliseconds == 0:
            raise ValueError(f"Audio file appears to be empty or corrupted: {video_path}")
        
        logger.info(f"Audio duration: {duration_in_milliseconds / 1000:.2f} seconds")
        
        # Segment audio into 10-minute chunks
        output_chunks = []
        current_pos = 0
        ten_minutes = 10 * 60 * 1000  # 10 minutes in milliseconds
        chunk_count = 0
        
        while current_pos < duration_in_milliseconds:
            try:
                chunk_end = min(current_pos + ten_minutes, duration_in_milliseconds)
                chunk_data = input_file[current_pos:chunk_end]
                
                # Use more reliable naming
                chunk_name = f"{video_chunk_base_name}_part{chunk_count:03d}{video_ext}"
                chunk_full_path = os.path.join(tmp_output_dir, chunk_name)
                
                logger.info(f"Exporting chunk {chunk_count + 1}: {chunk_name}")
                
                # Export chunk (remove format parameter to let pydub auto-detect)
                chunk_data.export(chunk_full_path)
                output_chunks.append(chunk_full_path)
                
                current_pos = chunk_end
                chunk_count += 1
                
                # Add memory cleanup
                del chunk_data
                
            except Exception as e:
                logger.error(f"Error processing chunk {chunk_count}: {str(e)}")
                raise
        
        logger.info(f"Successfully created {len(output_chunks)} audio chunks")
        return output_chunks, tmp_output_dir
        
    except Exception as e:
        logger.error(f"Error processing audio file {video_path}: {str(e)}")
        raise


def transcribe_video(video_path, client):
    """Transcribe a single audio file with error handling"""
    try:
        with open(video_path, "rb") as audio_file:
            logger.info(f"Transcribing: {os.path.basename(video_path)}")
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            return response
    except Exception as e:
        logger.error(f"Error transcribing {video_path}: {str(e)}")
        raise


def transcribe_videos_thread():
    """Start transcription in a separate thread"""
    global working
    working = True
    threading.Thread(target=transcribe_videos, daemon=True).start()
    hourglass_label["text"] = "Transcribing... |"
    root.after(100, animate_label)


def transcribe_videos():
    """Main transcription function with comprehensive error handling"""
    global video_paths, delete_audio_files, working
    
    try:
        # Validate API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            error_msg = "OPENAI_API_KEY environment variable not set!"
            logger.error(error_msg)
            update_completed_label("❌ Error: API key not found")
            update_completed_label("Please set OPENAI_API_KEY environment variable")
            working = False
            return
        
        # Create OpenAI client
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            logger.info("OpenAI client created successfully")
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {str(e)}")
            update_completed_label("❌ Error: Failed to initialize OpenAI client")
            working = False
            return
        
        # Process each video file
        total_files = len(video_paths)
        for i, video_path in enumerate(video_paths, 1):
            try:
                logger.info(f"Processing file {i}/{total_files}: {video_path}")
                update_completed_label(f"🎬 Processing {os.path.basename(video_path)} ({i}/{total_files})")
                
                # Basic file validation before attempting to process
                try:
                    file_size = os.path.getsize(video_path)
                    logger.info(f"File size check passed: {file_size / (1024*1024):.2f} MB")
                except Exception as e:
                    logger.error(f"Cannot access file {video_path}: {str(e)}")
                    update_completed_label(f"❌ Cannot access {os.path.basename(video_path)}: {str(e)}")
                    continue
                
                # Process audio and get chunks
                logger.info("Starting audio processing...")
                audio_chunks, tmp_output_dir = process_audio(video_path)
                logger.info(f"Audio processing completed. Generated {len(audio_chunks)} chunks.")
                
                # Transcribe all chunks (simplified, closer to original)
                full_transcription = ""
                for chunk_path in audio_chunks:
                    transcription_result = transcribe_video(chunk_path, client)
                    full_transcription += transcription_result
                
                # Save transcription (simplified path handling like original)
                save_file_path = video_path.replace(video_path.split("/")[-1], video_path.split("/")[-1].split(".")[0] + ".txt")
                utils.save_file(save_file_path, full_transcription)
                update_completed_label(save_file_path)
                logger.info(f"Transcription completed for: {save_file_path}")
                
                # Cleanup temporary files (like original)
                if delete_audio_files.get() == 1:
                    logger.info(f"Cleaning up temporary files in: {tmp_output_dir}")
                    shutil.rmtree(tmp_output_dir)
                
                # Ensure GUI updates are processed (like original)
                root.update_idletasks()
                
            except Exception as e:
                logger.error(f"Error processing file {video_path}: {str(e)}")
                update_completed_label(f"❌ Error processing {os.path.basename(video_path)}: {str(e)}")
                
                # Try to cleanup partial files
                try:
                    if 'tmp_output_dir' in locals() and os.path.exists(tmp_output_dir):
                        shutil.rmtree(tmp_output_dir)
                except:
                    pass
                
                continue
        
        
        update_completed_label("done!")
        logger.info("Transcription process completed")
        
    except Exception as e:
        logger.error(f"Fatal error in transcription process: {str(e)}")
        logger.error(traceback.format_exc())
        update_completed_label(f"❌ Fatal error: {str(e)}")
    
    finally:
        working = False
        logger.info("Worker thread finished")


#connect label to open file dialog so we can display the selected file path  
def update_label():
    def safe_label_update():
        try:
            if 'label' in globals() and label.winfo_exists():
                #clear the label first in case there are already files selected
                label["text"] = "Selected files:"
                #convert tuple to a string and remove the brackets and separate with newlines
                video_path_list = "\n".join(video_paths)
                label["text"] = label["text"] + "\n" + video_path_list
        except:
            pass  # Ignore GUI errors
    
    # Schedule on main thread if GUI exists
    if 'root' in globals():
        root.after(0, safe_label_update)
    else:
        safe_label_update()

# updates the completed_label text to concatenate the passed in file name separated by newline
def update_completed_label(file_name):
    global pending_messages
    # Thread-safe: just add to queue, main thread will process it
    pending_messages.append(file_name)

# open file dialog to allow user to select multiple files
def open_file_dialog():
    global video_paths
    # open a dile dialog to select multiple files. Allow either .mp4 or .mp3 files
    video_paths = filedialog.askopenfilenames(title = "Select files",filetypes = (("media files", "*.mp4 *.mp3 *.wav *.flac *.ogg *.aac *.aiff *.caf *.m4a")
,("all files","*.*")))
    if video_paths:
        print("Selected file:", video_paths)
        update_label()

def animate_label():
    global working, hourglass_label, root, pending_messages
    
    # Process pending GUI messages (safe - we're on main thread)
    while pending_messages:
        message = pending_messages.pop(0)
        try:
            completed_label["text"] = completed_label["text"] + "\n" + message
        except:
            pass  # Ignore GUI errors
    
    # get the current text
    current_text = hourglass_label["text"]
    # save the last character
    last_char = current_text[-1]
    #switch on the last character for the states '|', '/', '-', '\'
    if last_char == "|":
        new_text = current_text[:-1] + "/"
    elif last_char == "/":
        new_text = current_text[:-1] + "-"
    elif last_char == "-":
        new_text = current_text[:-1] + "\\"
    elif last_char == "\\":
        new_text = current_text[:-1] + "|"
    else:
        new_text = current_text + "|"
    
    # update the label
    hourglass_label["text"] = new_text
    # Process pending GUI updates (safe to call from main thread)
    root.update_idletasks()
    if working:
        # after 1 second, call animate_label again
        root.after(1000, animate_label)
    else:
        # clear the label
        hourglass_label["text"] = ""



def main():
    """Main function to run the GUI application"""
    global root, delete_audio_files, label, hourglass_label, completed_label
    
    root = tk.Tk()
    delete_audio_files = tk.IntVar()

    # Title the window
    root.title("Scribe")

    #button to open file dialog
    open_button = tk.Button(root, text="Open Media", command=open_file_dialog)
    open_button.pack(pady=10)

    # label that will display the selected file path
    label = tk.Label(root, text="Selected files:")
    label.pack(pady=10)

    # button to transcribe and save the file
    transcribe_button = tk.Button(root, text="Transcribe", command=transcribe_videos_thread)
    transcribe_button.pack(pady=10)

    # This is a label with text and an animated hourglass to indicate that the program is working
    hourglass_label = tk.Label(root, text="")
    hourglass_label.pack(pady=10)

    # add a UI checkmark to toggle whether the user wants to delete the processed audio files
    delete_audio_files_checkbutton = tk.Checkbutton(root, text="Cleanup temp files after transcription", variable=delete_audio_files)
    delete_audio_files_checkbutton.pack(pady=10)

    # label that will display the files that have completed transcription
    completed_label = tk.Label(root, text="Completed files:")
    completed_label.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()

