# scribe
Transcribes media files using OpenAI's Whisper API

This will create a UI that lets you use a filepicker to select multiple media files.
The supported filetypes are any common types shared by Whisper and pydub's Audiosegment
These include: *.mp4 *.mp3 *.wav *.flac *.ogg *.aac *.aiff *.caf and *.m4a
It will copy the file into smaller chunks to ensure they do not exceed Whisper's filesize limit.
You have the option of whether you want to keep the chunks or not.
It will then save the concatenated transcription to a .txt file

**Security Note:** This app now uses environment variables for API key storage instead of text files, which is much safer for protecting your credentials.

**API Update:** Updated to use the modern OpenAI Python library (v1.0+) with the new client-based approach for Whisper API calls.

**Reliability Improvements:** Added comprehensive error handling to prevent crashes:
- ✅ Graceful handling of missing API keys (no more crashes)
- ✅ Better memory management to prevent segmentation faults
- ✅ Individual chunk error recovery (one failed chunk won't stop the whole process)
- ✅ Proper cleanup of temporary files even when errors occur
- ✅ Detailed logging for troubleshooting issues

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

5. Install system dependencies (macOS with Homebrew)
   ```bash
   $ brew install ffmpeg tcl-tk
   ```
   
   **Note:** FFmpeg is required by `pydub` for audio file processing. On other systems:
   - **Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg python3-tk`
   - **Windows:** Use [Chocolatey](https://chocolatey.org/) or [Scoop](https://scoop.sh/) to install ffmpeg
   
6. Install the library dependencies
   ```bash
   $ pip3 install -r requirements.txt
   ```
   
   **Note:** This will install OpenAI library v1.0+ which has a different API structure than older versions. If you have an older version installed, you may need to upgrade.
   
   **Python 3.13+ Note:** If you're using Python 3.13+, the `audioop-lts` package will be automatically installed to replace the removed `audioop` module that `pydub` depends on.

7. Set your OpenAI API key as an environment variable

   Add your [OpenAI API key](https://beta.openai.com/account/api-keys) as an environment variable:

   **On macOS/Linux:**
   ```bash
   $ export OPENAI_API_KEY="your-api-key-here"
   ```

   **On Windows (Command Prompt):**
   ```cmd
   $ set OPENAI_API_KEY=your-api-key-here
   ```

   **On Windows (PowerShell):**
   ```powershell
   $ $env:OPENAI_API_KEY="your-api-key-here"
   ```

   For a permanent solution, add the environment variable to your shell profile (`.bashrc`, `.zshrc`, etc.) or system environment variables.

8. **Troubleshooting tkinter (GUI) issues:**
   
   If you get a `ModuleNotFoundError: No module named '_tkinter'` error, your Python installation doesn't have GUI support. This commonly happens with pyenv installations.
   
   **For pyenv users on macOS:**
   ```bash
   $ pyenv uninstall 3.13.5
   $ pyenv install 3.13.5
   ```
   
   **Alternative:** Use a different Python installation method like the official Python installer from python.org which includes tkinter by default.

9. Run scribe - the UI will let you pick the files you want to transcribe
    ```
    $ python transcribe.py
    ```

10. Don't forget to deactivate when you have finished!
   ```
   $ deactivate
   ```

## Troubleshooting

### Common Issues and Solutions

**Segmentation Fault/Crashes:**
- **Cause**: Usually memory issues with large audio files or corrupted files
- **Solution**: The app now has better memory management and will skip problematic files instead of crashing

**"No transcription generated" warnings:**
- **Cause**: Audio file may be corrupted, too quiet, or in an unsupported format
- **Solution**: Try converting the file to MP4 or MP3 format first

**GUI won't start:**
- **Cause**: Python installation missing tkinter support
- **Solution**: Follow the tkinter troubleshooting steps in section 8 above

**Transcription stops mid-process:**
- **Cause**: Network issues or OpenAI API rate limiting
- **Solution**: Check your internet connection and API quota. The app will now continue with remaining files even if one fails.
