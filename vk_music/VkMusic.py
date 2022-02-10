import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from vk_music.vk_audio.exc import *
from vk_music.vk_audio.VkAudio import VkAudio
from vk_api import VkApi
import config
from vk_music.Queues import Queues
from os.path import exists


class VkMusic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}
        self.queues = Queues()

        vk = VkApi(config.vk_login, config.vk_password)
        vk.auth()
        self.vk_audio = VkAudio(vk)

    @commands.command(name='join')
    async def _join(self, ctx: commands.Context):
        if ctx.message.author.voice:
            channel: discord.VoiceChannel = ctx.message.author.voice.channel
            voice = get(self.bot.voice_clients, guild=ctx.guild)

            if voice and voice.is_connected():
                if voice.channel.id != channel.id:
                    self.queues.remove(voice)
                    await voice.disconnect()
                    await channel.connect()
            else:
                await channel.connect()
        else:
            embed = discord.Embed(title='Error', color=discord.Color.red())
            embed.description = 'You are not in voice channel'
            await ctx.send(embed=embed)

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, song_name):
        await ctx.invoke(self._join)
        voice: discord.VoiceClient = get(self.bot.voice_clients, guild=ctx.guild)

        if voice:
            if self.queues.is_playing(voice):
                queue = self.queues.add_size(voice)
                audio = await self.prepare_audio(ctx, song_name, False, queue)
                if audio:
                    self.queues.add(voice, lambda: self.bot.loop.create_task(ctx.invoke(self.play, song_name=audio.path)))
                return

            self.queues.set_playing(voice, True)

            if not exists(song_name):
                audio = await self.prepare_audio(ctx, song_name)
                path = audio.path
            else:
                path = song_name

            voice.play(FFmpegPCMAudio(path, executable='/usr/bin/ffmpeg'),
                       after=self.get_after_func(ctx, voice, path))

    def get_after_func(self, ctx, voice, audio_path):
        # audio_path for loop
        return lambda x: self.queues.get(voice)() if not self.queues.is_looped(voice) else \
            self.bot.loop.create_task(ctx.invoke(self.play, song_name=audio_path))

    async def prepare_audio(self, ctx, song_name, play_now=True, queue_num=None):
        message = await ctx.send(':musical_note: Searching...')

        try:
            audio = self.vk_audio.download_song_by_name(song_name)
        except Exception as e:
            embed = discord.Embed(title='Error', color=discord.Color.red())

            if isinstance(e, AudioNotFoundException):
                msg = 'Song not found'
            elif isinstance(e, AssertionError):
                msg = 'Bad request'
            elif isinstance(e, AudioNotAvailable):
                msg = 'Audio not available'
            else:
                msg = 'Unknown error'
                print(e)

            embed.description = msg
            await message.delete()
            await ctx.send(embed=embed)
            return

        if play_now:
            embed = audio.get_discord_embed('Now Playing', ctx.author)
        else:
            embed = audio.get_discord_embed(f'Add in Queue#{queue_num}', ctx.author)
        await message.delete()
        await ctx.send(embed=embed)
        return audio

    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context):
        voice: discord.VoiceClient = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected() and voice.is_playing():
            voice.pause()
            self.queues.set_loop(voice, False)
            self.queues.get(voice)()
            embed = discord.Embed(title='Skiped', color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        voice: discord.VoiceClient = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            if voice.is_paused():
                title = 'Resume'
                voice.resume()
            else:
                title = 'Paused'
                voice.pause()
            embed = discord.Embed(title=title, color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='loop')
    async def loop(self, ctx: commands.Context):
        voice: discord.VoiceClient = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            val = not self.queues.is_looped(voice)
            self.queues.set_loop(voice, val)

            if val:
                title = 'Looped'
            else:
                title = 'Loop off'
            embed = discord.Embed(title=title, color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        voice: discord.VoiceClient = get(self.bot.voice_clients, guild=ctx.guild)
        self.queues.remove(voice)
        if voice and voice.is_connected():
            await voice.disconnect()
