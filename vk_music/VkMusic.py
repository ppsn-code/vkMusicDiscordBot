import discord
from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from vk_music.vk_audio.exc import *
from vk_music.vk_audio.VkAudio import VkAudio
from vk_api import VkApi
import config
from vk_music.Queues import Queues
from asyncio import run


class VkMusic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}
        self.queues = Queues()

        vk = VkApi(config.vk_login, config.vk_password)
        vk.auth()
        self.vk_audio = VkAudio(vk)

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        channel: discord.VoiceChannel = ctx.message.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            await channel.connect()

    @commands.command(name='play', invoke_without_subcommand=True)
    async def play(self, ctx: commands.Context, *, song_name):

        message = await ctx.send(':musical_note: Searching...')

        voice: discord.VoiceClient = get(self.bot.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            await message.delete()
            await ctx.send('Added in queue')
            self.queues.add(voice, lambda: run(ctx.invoke(self.play, song_name=song_name)))
            return

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
            return self.queues.get(voice)()

        await ctx.invoke(self._join)

        embed = audio.get_discord_embed('Now Playing', ctx.author)
        await message.delete()
        await ctx.send(embed=embed)

        voice.play(FFmpegPCMAudio(audio.path, executable='/usr/bin/ffmpeg'), after=lambda: self.queues.get(voice))

    @commands.command()
    async def leave(self, ctx: commands.Context):
        voice: discord.VoiceClient = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.disconnect()

