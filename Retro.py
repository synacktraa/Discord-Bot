#importing required modules

import discord
from discord.ext import commands
import json
import random
import wikipedia
import youtube_dl
from dotenv import load_dotenv
import os
import re, urllib.parse, urllib.request

load_dotenv() #loading the environment variable file


TOKEN = os.getenv("TOKEN") #setting the token value from the env file 

intents = discord.Intents().default()
intents.members = True #setting the discord intents for members to true

client = commands.Bot(command_prefix="$", intents=intents) #setting the command prefix to "$" and intents to intents

vowels = ['a','e','i','o','u'] #vowels list for editing the censored words
store = []

def emend(message, pattern, intent): #A recursive function which loops through the message and checks for censored words until it is free of censored words

    censor = pattern
    #this nested for loop will loop through the characters of the censored words and replace the vowels with an ascii character.
    for char in censor: 
        for v in vowels:
            if char == v:
                censor = censor.replace(char, '¿')
    edited = message.replace(pattern, censor) #edited variable is set to message after the censored words has been edited
    #this for loops check if there still is any censored words in edited messasge...if yes it will call the edit function again to replace the
    # censored word with the edited one until it's free of censored words.
    for pattern in intent:
        if pattern in edited:
            return emend(edited, pattern, intent)
    return edited  #finally returning the edited message

def get_url(name): #this function gets the best url for the name of the song or the 0th element of the search results
    
    query_string = urllib.parse.urlencode({"search_query": name}) #with this method we can get the search query 
    #if the song name is "Whatever Song Name" the query string will be "Whatever+Song+Name"
    formatUrl = urllib.request.urlopen("https://www.youtube.com/results?" + query_string) #Checking for results of the query
    #regex to find all possible url which is playable which then is stored in search_results list
    search_results = re.findall(r"watch\?v=(\S{11})", formatUrl.read().decode()) 
    #finally taking the 0th element as the video id and concatening it with th rest of the url
    url = "https://www.youtube.com/watch?v=" + "{}".format(search_results[0])     
    return url #returning the url

@client.event
async def on_ready(): #asynchronous function for discord bot to initialize
    activity = discord.Game(name="Zeroday.gg") #setting the activity variable to discord game 
    await client.change_presence(status=discord.Status.online, activity=activity) #when the bot is initialized the bot activity set to the activity provided
    print(f"Logged in as {client.user}.") 

@client.event
async def on_message(message): #on_message funtion which checks for the messages

    if message.author == client.user: #if author of the message is the bot itself it will not reply to it
        return
    
    #reading json files
    possibilities = json.loads(open("/mnt/e/Python/PROJECTS/Discord Bot/possibilities.json").read())
    replies = json.loads(open("/mnt/e/Python/PROJECTS/Discord Bot/replies.json").read())

    msg = message.content #setting the msg variable to message content
    channel = message.channel #channel variable to name of the channel in which message was sent

    author = str(message.author)
    authorName = ''
    #this for loop sets the authorName variable to author of the message excluding author id
    for let in author:
        if let != '#':
            authorName += let
        else:
            break

    if (len(msg) > 0): # checks if length of the msg is greater than 0
        try:
            if msg.startswith("$"):
                for intent in possibilities['intents']: #loops through the intents of possiblities json file 
                    for pattern in intent['greet']: #loops the greet dict from json file
                            if msg.startswith(f"${pattern}"): #if message starts with $+pattern in greet values
                                reply = random.choice(replies["greet"]) #sets the reply variable to random value from replies greet list
                                await channel.send(f"{reply} {authorName}") #sends the reply with the name of the author to greet the author
            else: #if message doesn't starts with the command prefix
                for intent in possibilities['intents']: #loops through the intents of possiblities json file 
                    intentConst = intent['swear'] #sets the intentConst to swear list
                    for pattern in intentConst: #loops through the swear list
                        if pattern in msg: #if the elements of swear list is in message emend function is called
                            outcome = emend(msg, pattern, intentConst) #outcome is set to emend function which will produce the edited message
                            await message.delete() #bot deletes the message which contains the censord message
                            await channel.send(f"[{authorName}] {outcome}") #bot sends the edited message with the author name
            
            
            
            await client.process_commands(message) #This function processes the commands that have been registered to the bot and other groups. 
            #Without this coroutine, none of the commands will be triggered.

        except discord.errors.NotFound:
            pass

        except discord.ext.commands.errors.CommandNotFound:
            pass

@client.event
async def on_member_join(member): #this function sends welcome message to the new member who joined in general chat and in their personal dm
    channel = discord.utils.get(client.get_all_channels(), name="general") #channel is set to general channel
    guild = channel.guild.name #guild variable is set to guild name 
    await channel.send(f"Welcome to the server, {member.mention} ! :partying_face:")
    await member.send(f"Welcome to the {guild} server, {member.name}.")

@client.command()
async def commands(ctx):
    msg = "$wiki <query> - for summary of a query.\n$echo <msg> - echoes the message back to the channel.\n$clear <num> - clear the num no. of messages.\n$play <song_name> - plays the song\n $pause - pauses the current playing audio.\n$resume - $resumes the stopped audio\n $leave - leaves the voice channel(before you play another song use $leave command)\n ${pattern}[patterns - hello, ciao, hey, hi] - greets the user."
    await ctx.send(msg)

@client.command()
async def echo(ctx, *msg): #this user defined bot function echoes the message. Usage $echo <msg> and the bot echoes <msg>
    msg = ' '.join(msg)
    await ctx.send(msg)

@client.command()
async def clear(ctx, lim: int): #this user defined bot function deletes the no. of messages provided by user. Usage $clear <no.>
    await ctx.channel.purge(limit=lim+1) #limit is set no. of messages +1, because the provided will be deleted too.

@clear.error 
async def clear_error(ctx, error): #this function checks for error in the $clear command
    if isinstance(error, commands.MissingRequiredArgument): #checks if an argument is missing
        await ctx.send("Usage: $clear <int>")
    elif isinstance(error, commands.BadArgument): #checks if the argument is integer value
        await ctx.send("Usage: $clear <int>")

@client.command()
async def wiki(ctx, *query): #this user defined function fetches the 2 line summary of the query from wikipedia provided by the user. 
    #Usage $wiki <query>
    query = " ".join(query) #as the query is taken as list...this joins the query elements with space between the elements 
    query = f'"{query}"' #query is set to query within double quotes as wikipedia module throws error or just doesn't provide information
    try:
        info = wikipedia.summary(query, 2) #info is set to the fetched summary of the query #2 here means how many lines we want it to fetch
        await ctx.send(info) #send the message the in the discord chat
    except wikipedia.exceptions.PageError: #if page is not found it sends the error
        error = "Page not found, Try something different!"
        await ctx.send(error)
    except wikipedia.exceptions.DisambiguationError as exc: #if there are more results of a query, it provides the list of possible query
        #which we can copy from the list and again run the command to get the summary
        await ctx.send(exc)
        await ctx.send("[Copy in same format and try again!]")

@client.command()
async def play(ctx, *name: str): #this function downloads the music in the server and play it on the discord channel

    name = " ".join(name) #name is changed to a string
    store.append(name) #song name is appended into store list

    url = get_url(name) #name is passed to the get_url function

    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name='Retro Space') #voice channel is set to General
    await voiceChannel.connect() #the bot is connected to the channel
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild) #voice to set to the guilds' voice client


    def ytdl(): #a function which downloads the song url from youtube 
        #[UHH FUCK IT, TIME CONSUMING AND IRRITATING FUNCTION]
        ydl_opts = { #setting some default youtube download options
            'format': 'bestaudio/best', #format for the best possible audio
            'postprocessors': [{
                'key': 'FFmpegExtractAudio', #key to extract audio
                'preferredcodec': 'mp3', #file type is set to mp3
                'preferredquality': '192', # quality is set to 192
            }],
        }

        songFile = os.path.isfile("song.mp3") #checks if there is song.mp3 file in the current directory and return true or false according to the result
        try:
            if songFile: #if true it removes the song.mp3 file
                os.remove("song.mp3")
        except PermissionError: #exception for permission error...if the music is still playing it won't be able to delete
            ctx.send("Wait for the current playing music to end or use the $stop command.") #sends this message if this function raises the permission error exception.
            return 
        
        with youtube_dl.YoutubeDL(ydl_opts) as ydl: 
            ydl.download([url]) #downloads the url
        for file in os.listdir('./'): #loops through the file in the current directory
            if file.endswith('.mp3'): #if a file ends with .mp3 it renames it to song.mp3, as youtube downloads the audio
                #with the name of the song, so this changes it to song.mp3, so that bot can play the current song.mp3
                os.rename(file, "song.mp3")
        voice.play(discord.FFmpegPCMAudio("song.mp3")) #voice client plays the song.mp3
        
    
    try:
        if ((store[-1]).lower()) == (store[-2].lower()): #checks if store last value is equals to store second last value
            voice.play(discord.FFmpegPCMAudio("song.mp3")) #if yes it plays the music without downloading anything as
            #both the values are same. [Time Saved -_-]
        else: #if both are not same it call the calls the ytdl() function which downloads the audio from youtube
            ytdl()
    except IndexError: #and if there is indexError that means user didn't asked anything yet to play and the both downloads the
        #audio from youtube
        ytdl()

@client.command()
async def leave(ctx): #this command tells the bot to leave the voice channel
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected(): #checks if the voice is connnected
        await voice.disconnect() # if yes it disconnects from the channel
    else: #else it prints the following message
        await ctx.send("I am not connected to any voice channel")

@client.command()
async def pause(ctx): #pauses the current playing audio
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing(): #checks if the voice is playing 
        voice.pause() #if yes it pauses the audio
    else: #else it sends the following message
        await ctx.send("Currently no audio is playing!")

@client.command()
async def resume(ctx): #it resumes the paused audio
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused(): #checks if the voice is paused
        voice.resume()# if yes it resumes the audio
    else: #else it send the following message
        await ctx.send("The audio is already playing.")

client.run(TOKEN) #client is runned with the parameter TOKEN which stored the token value of the both


