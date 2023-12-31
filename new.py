import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import speech_recognition as sr
from pydub import AudioSegment
import queue

# Initialize the audio_buffer in session_state
if "audio_buffer" not in st.session_state:
    st.session_state.audio_buffer = AudioSegment.empty()

# Initialize the speech recognizer
recognizer = sr.Recognizer()

with st.container():
    sample = st.session_state.audio_buffer
    audio_available = sample != AudioSegment.empty()
    if audio_available:
        st.audio(
            sample.export(format="wav", codec="pcm_s16le", bitrate="128k").read()
        )
        # Perform speech-to-text conversion
        with st.spinner(text="Performing speech-to-text conversion..."):
            try:
                text = recognizer.recognize_google(sample.export(format="wav").read())
                st.write("Speech-to-Text Conversion Result:")
                st.write(text)
            except sr.UnknownValueError:
                st.write("Unable to recognize speech.")
            except sr.RequestError as e:
                st.write(f"Speech recognition request error: {str(e)}")
    else:
        with (record_section := st.container()):
            webrtc_ctx = webrtc_streamer(
                key="sendonly-audio",
                mode=WebRtcMode.SENDONLY,
                audio_receiver_size=1024,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                },
                media_stream_constraints={"audio": True, "video": False},
            )

            with st.spinner(text="recording..."):
                while True:
                    if webrtc_ctx.audio_receiver:
                        audio_frames = []
                        try:
                            audio_frames = webrtc_ctx.audio_receiver.get_frames(
                                timeout=3
                            )
                        except queue.Empty:
                            record_section.write("no audio received...")
                        sound_chunk = AudioSegment.empty()
                        try:
                            for audio_frame in audio_frames:
                                sound = AudioSegment(
                                    data=audio_frame.to_ndarray().tobytes(),
                                    sample_width=audio_frame.format.bytes,
                                    frame_rate=audio_frame.sample_rate,
                                    channels=len(audio_frame.layout.channels),
                                )
                                sound_chunk += sound
                            if len(sound_chunk) > 0:
                                st.session_state.audio_buffer += sound_chunk
                        except UnboundLocalError:
                            # UnboundLocalError when audio_frames is not set
                            record_section.write("no audio detected...")
                    else:
                        break
