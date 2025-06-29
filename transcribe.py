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

# global variables
video_paths = ""
tmp_output_dir = ""
working = False

def process_audio(video_path):
    global tmp_output_dir
    # first let's create a directory to store the segmented audio files named after the video file
    # we'll use the video file name without the extension and replace space with underscore
    video_chunk_base_name = video_path.split("/")[-1].split(".")[0].replace(" ", "_") + "_chunks"
    # now let's save the file type
    video_file_type = video_path.split("/")[-1].split(".")[1]
    print("Creating directory:", video_chunk_base_name)
    # now let's capture the path where the file is located without the file name
    video_dir_path = video_path.replace(video_path.split("/")[-1], "")
    print("Video path:", video_dir_path)
    # create the directory and save the path
    tmp_output_dir = os.path.join(video_dir_path, video_chunk_base_name)
    print("Output directory:", tmp_output_dir)
    if not os.path.exists(tmp_output_dir):
        os.mkdir(tmp_output_dir)
    
    # now let's segment the audio into 10 minute chunks
    output_chunks = []
    input_file = AudioSegment.from_file(video_path)
    duration_in_milliseconds = len(input_file)
    current_pos = 0
    # PyDub handles time in milliseconds
    ten_minutes = 10 * 60 * 1000
    while current_pos < duration_in_milliseconds:
        chunk_data = input_file[current_pos:(current_pos+ten_minutes)]
        # let's name the chunk based on the video file name and the current position
        chunk_name = "{}_{}-{}.{}".format(video_chunk_base_name, current_pos, current_pos+ten_minutes,video_file_type)
        chunk_full_path = os.path.join(tmp_output_dir, chunk_name)
        output_chunks.append(chunk_full_path)
        chunk_data.export(chunk_full_path, format=video_file_type)
        current_pos += (ten_minutes - 1000) # subtract 1 second to avoid overlap
    return output_chunks


# this function transcribes the video file to a text file using the openAI API.
def transcribe_video(video_path, client):
    # load the model
    with open(video_path, "rb") as audio_file:
        return client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

def transcribe_videos_thread():
    global working
    working = True
    threading.Thread(target=transcribe_videos).start()
    hourglass_label["text"] = "Transcribing... |"
    root.after(100, animate_label)

# This function transcribes the video file to a text file using the openAI API.
def transcribe_videos():
    global video_paths, tmp_output_dir, delete_audio_files, working
    # load the openAI key from environment variable and create client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key as an environment variable.")
        update_completed_label("Error: OPENAI_API_KEY not set!")
        working = False
        return
    
    # Create OpenAI client
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    # for each video file, transcribe it and save the output to a text file using the original file name with .txt extension
    for video_path in video_paths:
        print("Transcribing video:", video_path)
        # convert the audio and segment if necessary
        audio_chunks = process_audio(video_path)

        full_transcription = ""
        for path in audio_chunks:
            # transcribe the video
            transcription_result = transcribe_video(path, client)
            # append the transcription to the full transcription
            full_transcription += transcription_result
        
        # save the transcription to a text file replacing the type with .txt
        save_file_path = video_path.replace(video_path.split("/")[-1], video_path.split("/")[-1].split(".")[0] + ".txt")
        utils.save_file(save_file_path, full_transcription)
        # update the completed_label with the file name
        update_completed_label(save_file_path)
        print("Transcription complete for:", save_file_path)
        #cleanup the segmented audio files
        if delete_audio_files.get() == 1:
            print("Cleaning up temporary files in:", tmp_output_dir)
            shutil.rmtree(tmp_output_dir)
        #ensure print buffers flush before next loop
        root.update_idletasks()
    update_completed_label("done!")
    tmp_output_dir = ""
    working = False


#connect label to open file dialog so we can display the selected file path
def update_label():
    #clear the label first in case there are already files selected
    label["text"] = "Selected files:"
    #convert tuple to a string and remove the brackets and separate with newlines
    video_path_list = "\n".join(video_paths)
    label["text"] = label["text"] + "\n" + video_path_list

# updates the completed_label text to concatenate the passed in file name separated by newline
def update_completed_label(file_name):
    completed_label["text"] = completed_label["text"] + "\n" + file_name

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
    global working, hourglass_label, root
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
    #ensure print buffers flush before next loop
    root.update_idletasks()
    if working:
        # after 1 second, call animate_label again
        root.after(1000, animate_label)
    else:
        # clear the label
        hourglass_label["text"] = ""



root = tk.Tk()
delete_audio_files = tk.IntVar()

# Title the window
root.title("Scribe")

#button to open file dialog
open_button = tk.Button(root, text="Open Video", command=open_file_dialog)
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

