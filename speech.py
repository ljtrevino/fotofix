from __future__ import division

import functools
import os
import re
import sys
import time

from google.cloud import speech
from google.cloud import texttospeech
from google.cloud.speech import enums
from google.cloud.speech import types
from playsound import playsound
from playsound import PlaysoundException
import pyaudio
from six.moves import queue

from commands import actions, all_words, commands, edit_modes, terminator

# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms


def get_current_time():
    """Return Current Time in MS."""

    return int(round(time.time() * 1000))


class ResumableMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk_size):
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()
        self.restart_counter = 0
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

    def __enter__(self):

        self.closed = False
        return self

    def __exit__(self, type, value, traceback):

        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, *args, **kwargs):
        """Continuously collect data from the audio stream, into the buffer."""

        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        """Stream Audio from microphone to API and to local buffer"""

        while not self.closed:
            data = []

            if self.new_stream and self.last_audio_input:

                chunk_time = STREAMING_LIMIT / len(self.last_audio_input)

                if chunk_time != 0:

                    if self.bridging_offset < 0:
                        self.bridging_offset = 0

                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time

                    chunks_from_ms = round((self.final_request_end_time -
                                            self.bridging_offset) / chunk_time)

                    self.bridging_offset = (round((
                        len(self.last_audio_input) - chunks_from_ms)
                                                  * chunk_time))

                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        data.append(self.last_audio_input[i])

                self.new_stream = False

            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            self.audio_input.append(chunk)

            if chunk is None:
                return
            data.append(chunk)
            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)

                    if chunk is None:
                        return
                    data.append(chunk)
                    self.audio_input.append(chunk)

                except queue.Empty:
                    break

            yield b''.join(data)


def process(responses, tts_client, voice, audio_config, stream, widget):
    """Iterates through server responses and processes them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.
    """
    audio_path = "audio/"
    if not os.path.exists(audio_path):
        os.makedirs(audio_path)
    
    for response in responses:

        if get_current_time() - stream.start_time > STREAMING_LIMIT:
            stream.start_time = get_current_time()
            break
        
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        if result.is_final:
            stream.is_final_end_time = stream.result_end_time
            stream.last_transcript_was_final = True

            # Display the transcription of the top alternative
            transcript = result.alternatives[0].transcript
            parsed = transcript.strip().lower()
            # print("Parsed: ", parsed)
            words = set(parsed.split())

            # Adjust time for endless streaming
            result_seconds = 0
            result_nanos = 0

            if result.result_end_time.seconds:
                result_seconds = result.result_end_time.seconds

            if result.result_end_time.nanos:
                result_nanos = result.result_end_time.nanos

            stream.result_end_time = int((result_seconds * 1000)
                                        + (result_nanos / 1000000))

            # Handles command phrases of varying length: 
            #   1 edit mode and/or 1 action

            # Find the edit mode
            command = words.intersection(commands.keys())  # Check speech input against synonyms
            # print("Command: ", command)
            if command:
                repeatables = ('undo', 'redo', 'rotate')
                command = list(command)[0]
                mode = commands[command]
                if (widget.mode != mode) or (mode in repeatables):
                    # print(len(widget.picture.history))
                    # print(widget.picture.history_pos)
                    process_word(widget, audio_path, tts_client, voice, audio_config, mode)

            # Find the action to take
            if widget.mode in edit_modes and widget.mode in actions:
                mode = widget.mode
                action = words.intersection(actions[mode].keys())
                # print("Action: ", action)
                if action: 
                    action = list(action)[0]
                    action = actions[mode][action]  # Get action keyword
                    process_word(widget, audio_path, tts_client, voice, audio_config, mode, action)
            
            # If an exit keyword is spoken, the entire program terminates
            exit_keyword = words.intersection(terminator)
            if exit_keyword:
                exit_keyword = list(exit_keyword)[0]
                widget.on_speech_recognized(exit_keyword)
                sys.exit()


def process_word(widget, audio_path, tts_client, voice, audio_config, mode, action=None):
    if mode in ('sticker', 'transparent') and action:  # Handles audio for applying stickers/transparent background
        widget.on_speech_recognized(action)
        audio_fname = audio_path + 'apply_' + mode + '.mp3'
        play_audio_feedback(widget, audio_fname, tts_client, voice, audio_config, action=action)
    
    elif mode in ('brightness', 'contrast', 'pixelate', 'saturation', 'sharpness', 'zoom') and action:  # Handles audio for slider/zoom actions
        widget.on_speech_recognized(action)
    
    elif mode in ('undo', 'redo'):
        widget.on_speech_recognized(mode)
        picture = widget.picture
        is_original_image = picture.is_original_image()
        is_latest_image = picture.is_latest_image()
        if mode == 'undo' and is_original_image:
            audio_fname = audio_path + 'original.mp3'
        elif mode == 'redo' and is_latest_image:
            audio_fname = audio_path + 'latest.mp3'
        else:
            audio_fname = audio_path + mode.replace(' ', '_') + '.mp3'
        play_audio_feedback(widget, audio_fname, tts_client, voice, audio_config)

    elif mode == 'rotate':
        if widget.mode == 'rotate':  # Check if in rotate mode
            audio_fname = audio_path + 'rotating.mp3'
            is_rotating = True
            # Turning image
        else:
            audio_fname = audio_path + 'rotation.mp3'
            is_rotating = False
            # Now entering rotation mode
        widget.on_speech_recognized(mode)
        play_audio_feedback(widget, audio_fname, tts_client, voice, audio_config, action=None, is_rotating=is_rotating)

    else:  # Handles audio for switching between modes
        widget.on_speech_recognized(mode)
        audio_fname = audio_path + mode.replace(' ', '_') + '.mp3'
        play_audio_feedback(widget, audio_fname, tts_client, voice, audio_config)


def play_audio_feedback(widget, audio_fname, tts_client, voice, audio_config, action=None, is_rotating=None):
    try:
        playsound(audio_fname)
    except PlaysoundException:                        
        synthesize_audio(widget, audio_fname, tts_client, voice, audio_config, action, is_rotating)
        playsound(audio_fname)
    except Exception as e: 
        print("Exception")
        print(e)


def synthesize_audio(widget, audio_fname, tts_client, voice, audio_config, action=None, is_rotating=None):
    mode = widget.mode
    # Set the text input to be synthesized
    if mode in edit_modes:
        if mode == 'transparent':
            if action:
                text = mode + " background has been added"
            else: 
                text = "Now entering " + mode + " background mode"
        elif mode == 'sticker' and action:
            text = mode + " has been applied"
        elif mode in ('invert', 'grayscale'):
            text = mode + "ing image"
        elif mode == 'rotate':
            if is_rotating:
                text = "Turning image"
            else:
                text = "Now entering rotation mode"
        else: 
            text = "Now entering " + mode + " mode"
    elif mode in ('undo', 'redo'): 
        picture = widget.picture
        is_original_image = picture.is_original_image()
        is_latest_image = picture.is_latest_image()
        if (mode == 'undo' and is_original_image) or (mode == 'redo' and is_latest_image):
            text = "No changes left to be " + mode + "ne"
        text = "Latest change has been " + mode + "ne"
    elif mode == 'save':
        text = "Changes have been " + mode + "d"

    synthesis_input = texttospeech.types.SynthesisInput(text=text)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = tts_client.synthesize_speech(synthesis_input, voice, audio_config)

    # The response's audio_content is binary
    with open(audio_fname, 'wb') as out:
        # Write the response to the output file
        out.write(response.audio_content)
        print('Audio content written to file "' + audio_fname + '"')


def speech_main(widget):
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'en-US'  # a BCP-47 language tag
    
    stt_client = speech.SpeechClient()
    tts_client = texttospeech.TextToSpeechClient()
    phrases = list(functools.reduce(lambda x, y: x.union(y.keys()), all_words, set()))
    speech_context = speech.types.SpeechContext(phrases=phrases)
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code=language_code,
        speech_contexts=[speech_context])
    streaming_config = speech.types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)
    
    # Build the voice request, select the language code, and the voice gender
    voice = texttospeech.types.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)

    # Select the type of audio file returned
    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
    with mic_manager as stream:
        while not stream.closed:
            stream.audio_input = []
            audio_generator = stream.generator()

            requests = (speech.types.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)

            responses = stt_client.streaming_recognize(streaming_config, requests)

            # Now, put the transcription responses to use.
            process(responses, tts_client, voice, audio_config, stream, widget)

            if stream.result_end_time > 0:
                stream.final_request_end_time = stream.is_final_end_time
            stream.result_end_time = 0
            stream.last_audio_input = []
            stream.last_audio_input = stream.audio_input
            stream.audio_input = []
            stream.restart_counter = stream.restart_counter + 1

            if not stream.last_transcript_was_final:
                sys.stdout.write('\n')
            stream.new_stream = True