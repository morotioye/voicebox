import io
import logging
import pydub  # pip install pydub
import discord
from discord.sinks import MP3Sink
from datetime import datetime, timezone
import asyncio
from google.cloud import speech, texttospeech
import openai

class Voicebox:
    def __init__(self, token):
        self.voice_connections = {}
        self.conversations = {}
        self.vc = None
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
            await ctx.channel.send("Ready.")

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

        @self.bot.command(description="Join voice channel.")
        async def join(interaction):
            user_id = interaction.user.id
            self.vc = await self.voice_channel.connect()
            await interaction.response.send_message("Joined the voice channel.")
        
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
            
            elif self.conversing:
                self.conversing = False
                self.script = self.lens.get_script()
                await ctx.respond("Conversation has stopped.")
            else:
                await ctx.respond("I wasn't transcribing.")
        
                

        @self.bot.command(description="Begin a conversation with bot.")
        async def converse(interaction):
            # Method to converse with GPT
            self.conversing = True
            await interaction.response.send_message("Conversation started! Unmute to begin talking.")

        @self.bot.command(description="Stop the current voice response.")
        async def stopaudio(ctx):
            """Stop the currently playing audio in the voice channel."""
            vc: discord.VoiceClient = ctx.voice_client

            if not vc or not vc.is_playing():
                await ctx.send("There is no audio currently playing.")
                logging.info("No audio is playing right now.")
            else:
                vc.stop()
                await ctx.respond("Stopped the audio playback.")
                logging.info("Audio playback stopped.")
        
        @self.bot.event
        async def on_voice_state_update(member, before, after):
            if self.transcribing or self.conversing:# Ignore if the member is the bot itself
                if member == self.bot.user:
                    return

                # Check if the member's voice state changed in terms of self_mute
                if before.self_mute == after.self_mute:
                    return

                # Get the user's thread data to find the corresponding text channel
                thread_data = self.monitor.get_thread(member.id)
                if not thread_data:
                    return

                text_channel_id = thread_data[1]
                text_channel = self.bot.get_channel(text_channel_id)

                # Check if the user muted or unmuted themselves and send a message accordingly
                if after.self_mute:  # If the user muted themselves
                    await text_channel.send(f"{member.name} muted themselves.")
                    logging.info(f"{member.name} MUTED BY {member.name}")
                    await self.stop_recording(member)
                else:  # If the user unmuted themselves
                    await text_channel.send(f"{member.name} unmuted themselves.")
                    logging.info(f"{member.name} UNMUTED BY {member.name}")
                    await self.start_recording(member, text_channel)


    async def start_recording(self, member, text_channel):
        if self.monitor.voice_status:
            return  # Already recording

        voice = member.voice
        if not voice:
            return

        vc: discord.VoiceClient = voice.channel.guild.voice_client
        if not vc:
            return

        if not discord.opus.is_loaded():
            # discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.4/lib/libopus.0.dylib')
            logging.info("OPUS NOT REQUIRED")

        # Start recording and pass the finished_callback with the text_channel
        vc.start_recording(
            MP3Sink(),
            self.finished_callback, 
            text_channel
            
        )
        self.monitor.voice_status = True
        logging.info(f"Started recording for member {member.id}")

    async def stop_recording(self, member):
        if not self.monitor.voice_status:
            return  # Not recording

        voice = member.voice
        if not voice:
            return

        vc: discord.VoiceClient = voice.channel.guild.voice_client
        if not vc:
            return

        vc.stop_recording()
        self.monitor.voice_status = False
        logging.info(f"Stopped recording for member {member.id}")

    async def respond(self, transcription_text: str, user_id: int):
        """Converts the transcription text to speech and plays it in the voice channel."""
        
        # Check if there's an existing conversation for the user
        if user_id not in self.conversations:
            self.conversations[user_id] = [{"role": "system", "content":f"{self.monitor.system_message}"}]
        
        # Add the user's message to the conversation history
        self.conversations[user_id].append({"role": "user", "content": transcription_text})

        # Get a response from GPT-3
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.conversations[user_id]
            ).choices[0].message.content
            
            logging.info("RESPONSE GENERATED")
        except Exception as e:
            print(e)

        # Add the assistant's response to the conversation history
        self.conversations[user_id].append({"role": "assistant", "content": response})

        # Initialize the Text-to-Speech client
        self.tts_client = texttospeech.TextToSpeechClient.from_service_account_json('key.json')

        # Set the text input and audio configuration
        synthesis_input = texttospeech.SynthesisInput(text=response)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-AU",
            name="en-AU-Wavenet-C",
            # ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            effects_profile_id=["small-bluetooth-speaker-class-device"],
            pitch=0,
            speaking_rate=1
        )

        # Generate the speech audio
        try:
            audio_response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logging.info("RESPONSE AUDIO GENERATED")
        except Exception as e:
            print(e)
        
        # Save the audio to a file
        with open("output.wav", "wb") as out:
            out.write(audio_response.audio_content)

        # Play the audio in the voice channel
        if self.vc:  # Assuming self.vc is your VoiceClient instance
            self.vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source="output.wav"))
            logging.info(f"Responded to user {user_id} with message: f{response}")
            self.lens.sys_msg(message=response)
                
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
        await channel.send(transcription)
        self.lens.user_msg(transcription)
        print(type(self.lens))

        # Respond to the last transcription
        await self.respond(transcription, user_id) # TODO -- change this for splitting transcription & conversing
        logging.info("Transcription logged")


    def start(self):
        self.bot.run(self.monitor.bot_token)
        logging.info("Bot started running")
 #
