# scribe
Transcribes media files using OpenAI's Whisper API

This will create a UI that lets you use a filepicker to select multiple media files.
The supported filetypes are any common types shared by Whisper and pydub's Audiosegment
These include: *.mp4 *.mp3 *.wav *.flac *.ogg *.aac *.aiff *.caf and *.m4a
It will copy the file into smaller chunks to ensure they do not exceed Whisper's filesize limit.
You have the option of whether you want to keep the chunks or not.
It will then save the concatenated transcription to a .txt file
** As of 07/16 I have not built any robust error handling into as of yet, so use at your own risk **

## Setup and Running Scribe

1. If you don’t have Python installed, [install it from here](https://www.python.org/downloads/)

    Documentation for the [OpenAI's Whisper API is available here.](https://platform.openai.com/docs/guides/speech-to-text)


2. Clone this repository

   ```bash
   $ git clone git@github.com:csymonds/scribe.git
   ```

3. Navigate into the project directory
   
   ```bash
   $ cd scribe
   ```

4. Virtualize (Note: Non-Windows users will see `venv/bin/activate`)
   ```
   $ python -m venv venv
   $ . venv/Scripts/activate
   ```

5. Install the library dependencies
   ```bash
   $ pip3 install -r requirements.txt
   ```

6. Add your OpenAI key to use whisper

   Step 1: Make a copy of the example environment variables files

   ```bash
   $ cp example_key_openai.txt key_openai.txt
   ```

   Step 2: Copy in your key to the respective file

    Add your [OpenAI API key](https://beta.openai.com/account/api-keys) to the newly created `key_openai.txt` file

7. Run scribe - the UI will let you pick the files you want to transcribe
    ```
    $ python.exe .\transcribe.py
    ```

7. Don't forget to deactivate when you have finished!
   ```
   $ deactivate
   ```
