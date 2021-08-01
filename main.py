import discord
from discord.ext import commands
from pymongo import MongoClient
from asyncio import TimeoutError
from secrets import token_hex
from datetime import datetime
import json

client = commands.Bot(command_prefix="-")
tokens = json.load(open("tokens.json"))
mc = MongoClient(tokens["mongo"])
db = mc["Storee"]
books = db["books"]
chapters = db["chapters"]
authors = db["authors"]
tags = ["anime", "fanfic", "blog", "nsfw", "teen", "children", "horror", "adventure", "comedy", "thriller", "other"]
days = {1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday", 7: "Saturday"}
months = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
blue = 0x113EB0

async def err(ctx, cmd):
    await ctx.send(f"You took too long lmao now do {cmd} again")

@client.event
async def on_ready():
    print("Ready.")

@client.command()
async def ping(ctx):
    await ctx.send(f"Ping: `{round(client.latency, 4) * 1000}ms`.")

@client.command()
async def new(ctx, bc=None, name=None):

    async def asktags(ctx):
        tags = []

        e = discord.Embed(
            title="What tags does your book have? (max 3, split using commas)",
            description="Available tags:\n\nAnime, Fanfic, Blog, NSFW, Teen, Children, Horror, Adventure, Comedy, Thriller, Other\n\nSuggest more tags! DM aryamaan.exe#8953 to suggest (no spam kthxbai)",
            color=blue
        )
        e.set_footer(text="For example: Anime, Teen, Adventure. Note that the space is required :P")
        await ctx.send(embed=e)

        try:
            msg = await client.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        except TimeoutError:
            await err(ctx, "-new")
        else:
            tagsl = msg.content.lower.split(", ")
            for t in tagsl:
                if t not in tagsl:
                    await ctx.send("Couldn't find that tag (maybe you didn't split tags with a comma and space?)")
                    await asktags(ctx)
                    break
                else:
                    tags.append(t)

        return tags        

    async def book(ctx):
        b_id = token_hex(4)
        await ctx.send("What's your book's name?")
        try:
            msg = await client.wait_for("message", timeout=40, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        except TimeoutError:
            await err(ctx, "-new")
        else:
            name = msg.content
            if books.find_one({"name": name}) != None:
                return await ctx.send("You already have a book by that name-")
            tags = await asktags(ctx) # More splitting stuff into functions to avoid lines with a million indents ᕕ(ᐛ)ᕗ

        n = datetime.now()
        d = days[n.day]
        dt = n.date
        m = months[n.month]
        y = n.year
        date = f"{d}, {dt} {m} {y}"
        books.insert_one({"_id": b_id, "name": name, "author": ctx.author.id, "tags": tags, "date": date, "chapters": []})
        
        e = discord.Embed(
            title="Made your book!",
            description=name + " is now published :D\nAdd chapters using -new\nYour book ID is " + b_id + " (best to keep it somewhere just in case)",
            color=blue
        )
        await ctx.send(embed=e)

    async def chapter(ctx):
        query = books.find({"author": ctx.author.id})
        book = None
        if not query:
            return await ctx.send("You don't have any books lmao\nDo -new to make a new book :P")
        elif len(query) == 1:
            book = query[0]
        else:
            await ctx.send("Which book is this chapter for? (name or ID works)")
            try:
                msg = await client.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            except TimeoutError:
                await err(ctx, "-new")
            else:
                q = msg.content

        if book == None:
            book = books.find_one({"_id": q})
            if book == None:
                book = books.find_one({"name": q, "author": ctx.author.id})
                if book == None:
                    return await ctx.send("Didn't find any book by that name :/\nTry -new again")
        
        await ctx.send("What is the name of the chapter?")
        try:
            msg = await client.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        except TimeoutError:
            await err(ctx, "-new")
        else:
            q = msg.content
            if chapters.find_one({"author": ctx.author.id, "name": name}) != None:
                return await ctx.send("That chapter already exists lmao do -new again")

        chaps = book["chapters"]
        c_id = token_hex(5)
        chaps.append(c_id)
        await books.update_one({"_id": book["_id"]}, {"$set": {"chapters": chaps}})
        await chapters.insert_one({"_id": c_id, "name": name, "author": ctx.author.id, "book": book["_id"], "content": ""})

        e = discord.Embed(
            title="Your chapter has been created!",
            description="Use -write to add to this chapter",
            color=blue
        )
        
        e.set_footer(text="Note- if you want to keep your chapter content a secret, DM this bot with -add")
        await ctx.send(embed=e)
    
    await ctx.send("Are you creating a book or chapter? (type book/chapter)")
    try:
        msg = await client.wait_for("message", timeout=20, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
    except TimeoutError:
        await err(ctx, "-new")
    else:
        if msg.content.lower() in ["b", "book"]:
            await book(ctx)
        elif msg.content.lower() in ["c", "chapter"]:
            await chapter(ctx)
        else:
            await ctx.send("Type book or chapter lmao\nPS you can even do b or c >:)")

@client.command(aliases=["add"])
async def write(ctx):
    await ctx.send("Which chapter do you wanna write to? Name or ID works")
    # Will commit tomorrow lmao

client.run(tokens["bot"])