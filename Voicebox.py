import io
import logging
import pydub  # pip install pydub
import discord
from discord.ext import commands
from discord.sinks import MP3Sink
import tempfile  # Add this import
import os
from ATS import ATS
import asyncio
from google.cloud import speech, texttospeech

class Voicebox:
    def __init__(self, token):
        self.voice_connections = {}
        self.conversations = {}
        self.token = token
        self.voice_status = False
        self.vc = None
        self.ats = ATS()
        self.client = speech.SpeechClient.from_service_account_json('key.json')
        self.transcribing = False
        self.conversing = False

        self.bot = discord.Bot(command_prefix='!', intents=discord.Intents.all())
        self.token = token
        logging.info('Controller initialized')

        @self.bot.event
        async def on_ready():
            print(f"Logged in as {self.bot.user}")
            logging.info(f"Logged in as {self.bot.user}")

        @self.bot.command(description="Check status")
        async def status(ctx):
            await ctx.channel.send("Voicebox ready.")

        @self.bot.command(description="Speak text into a voice channel.")
        async def speak(interaction, message: str):
            if not discord.opus.is_loaded():
                discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.4/lib/libopus.0.dylib')
            
            await interaction.response.send_message(message)
            # init client
            self.tts_client = texttospeech.TextToSpeechClient.from_service_account_json('key.json')
            synthesis_input = texttospeech.SynthesisInput(text=message)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-AU",
                name="en-AU-Wavenet-C",
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                effects_profile_id=["small-bluetooth-speaker-class-device"],
                pitch=0,
                speaking_rate=1
            )

            try:
                audio_response = self.tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
            except Exception as e:
                print(e)
            
            # Save the audio to a file
            with open("output.wav", "wb") as out:
                out.write(audio_response.audio_content)

            # Play the audio in the voice channel
            if self.vc:  # Assuming self.vc is your VoiceClient instance
                self.vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="output.wav"))
                logging.info("it worked")

        @self.bot.command(description="Recognize ASL and speak it.")
        async def recognize(interaction):
            await interaction.response.send_message("before")
            self.ats.start()
            reply_mess = ""
            arr = self.ats.message_array
            temp_string = ""
            for i in range(len(arr)):
                if arr[i] != temp_string:
                    temp_string = arr[i]
                    reply_mess += arr[i]

            reply_mess += "."
            await interaction.channel.send(reply_mess)

            if not discord.opus.is_loaded():
                discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.4/lib/libopus.0.dylib')
            # init client
            self.tts_client = texttospeech.TextToSpeechClient.from_service_account_json('key.json')
            synthesis_input = texttospeech.SynthesisInput(text=reply_mess)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-AU",
                name="en-AU-Wavenet-C",
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                effects_profile_id=["small-bluetooth-speaker-class-device"],
                pitch=0,
                speaking_rate=1
            )

            try:
                audio_response = self.tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
            except Exception as e:
                print(e)
            
            # Save the audio to a file
            with open("output.wav", "wb") as out:
                out.write(audio_response.audio_content)

            # Play the audio in the voice channel
            if self.vc:  # Assuming self.vc is your VoiceClient instance
                self.vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="output.wav"))
                logging.info("it worked")
            
            

        @self.bot.command(description="Clear channel of messages.")
        async def clear(interaction):
            # TODO add InterBot developer role and have this check for that
            if interaction.user.guild_permissions.administrator:  # Check for admin permissions
                channel = interaction.channel  # Get channel
                await interaction.response.send_message("Starting...")  # Confirm deletion
                
                # Fetch messages and delete them
                async for message in channel.history(limit=None):
                    await asyncio.sleep(0.3)  # Respect rate limit
                    await message.delete()  # Delete message

            else:  # If user is not an admin
                await interaction.response.send_message("Sorry, you do not have the perms for this.")  # Error message

        @self.bot.command(description="Connect to voice channel.")
        async def connect(interaction):
            # Check if the user is in a voice channel
            if interaction.author.voice and interaction.author.voice.channel:
                channel = interaction.author.voice.channel
                self.vc = await channel.connect()
                await interaction.response.send_message("Joined the voice channel.")
            else:
                await interaction.response.send_message("You are not connected to a voice channel.")

        @self.bot.slash_command(description="Disconnect from voice channel.")
        async def disconnect(interaction):
            await self.vc.disconnect()
            await interaction.response.send_message("Disconnected.")
        
        @self.bot.command(description="Transcribe our voice channel.")
        async def transcribe(interaction):
            """Transcribe the voice channel"""
            self.transcribing = True
            await interaction.response.send_message("Transcription started!")
 
        @self.bot.command(description="Stop transcription.")
        async def stop(ctx: discord.ApplicationContext):
            """Stop the recording"""
            vc: discord.VoiceClient = ctx.voice_client

            if not vc:
                return await ctx.respond("There's no action going on right now")

            if self.transcribing:
                self.transcribing = False
                await ctx.respond("The transcription has stopped.")
            
            else:
                await ctx.respond("I wasn't transcribing.")
        
        @self.bot.event
        async def on_voice_state_update(member, before, after):
            if self.transcribing:# Ignore if the member is the bot itself
                if member == self.bot.user:
                    return

                # Check if the member's voice state changed in terms of self_mute
                if before.self_mute == after.self_mute:
                    return

                text_channel = self.bot.get_channel(1155234947053912175)

                # Check if the user muted or unmuted themselves and send a message accordingly
                if after.self_mute:  # If the user muted themselves
                    logging.info(f"{member.name} MUTED BY {member.name}")
                    await self.stop_recording(member)
                else:  # If the user unmuted themselves
                    logging.info(f"{member.name} UNMUTED BY {member.name}")
                    await self.start_recording(member, text_channel)

    async def start_recording(self, member, text_channel):
        if self.voice_status:
            return  # Already recording

        voice = member.voice
        if not voice:
            return

        vc: discord.VoiceClient = voice.channel.guild.voice_client
        if not vc:
            return

        if not discord.opus.is_loaded():
            discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.4/lib/libopus.0.dylib')


        # Start recording and pass the finished_callback with the text_channel
        vc.start_recording(
            MP3Sink(),
            self.finished_callback, 
            text_channel
            
        )
        self.voice_status = True
        logging.info(f"Started recording for member {member.id}")

    async def stop_recording(self, member):
        if not self.voice_status:
            return  # Not recording

        voice = member.voice
        if not voice:
            return

        vc: discord.VoiceClient = voice.channel.guild.voice_client
        if not vc:
            return

        vc.stop_recording()
        self.voice_status = False
        logging.info(f"Stopped recording for member {member.id}")
                
    # Finish callback for /converse
    async def finished_callback(self, sink: MP3Sink, channel: discord.TextChannel):
        mention_strs = []
        audio_segs: list[pydub.AudioSegment] = []

        longest = pydub.AudioSegment.empty()

        for user_id, audio in sink.audio_data.items():
            mention_strs.append(f"<@{user_id}>")

            seg = pydub.AudioSegment.from_file(audio.file, format="mp3")

            # Determine the longest audio segment
            if len(seg) > len(longest):
                audio_segs.append(longest)
                longest = seg
            else:
                audio_segs.append(seg)

        for seg in audio_segs:
            longest = longest.overlay(seg)

        # Convert the audio to mono
        longest = longest.set_channels(1)

        # Convert the audio to raw PCM data
        buffer = io.BytesIO()
        longest.export(buffer, format="wav", codec="pcm_s16le")
        buffer.seek(0)
        content = buffer.read()

        # Transcribe the audio
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="en-US",
            enable_automatic_punctuation = True
        )

        response = self.client.recognize(config=config, audio=audio)
        transcription = ''.join([result.alternatives[0].transcript for result in response.results])

        # Send the transcription to the Discord channel
        user = await self.bot.fetch_user(user_id)
        await channel.send(f"**{user.name}: **" + transcription) # should have use
    def start(self):
        self.bot.run(self.token)
        logging.info("Bot started running")

    def daddy(self, arr):
        if not arr or len(arr) < 2:
            return arr
        
        result = []
        i = 0
        while i < len(arr) - 1:
            if arr[i] == arr[i + 1]:
                i += 2  # skip the next element
            else:
                result.append(arr[i])
                i += 1
        
        # Handle the last element if it's not part of a duplicate pair
        if i == len(arr) - 1:
            result.append(arr[i])
        
        return result