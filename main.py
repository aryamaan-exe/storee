import discord
from discord.ext import commands
from pymongo import MongoClient
from asyncio import TimeoutError
from secrets import token_hex
from datetime import datetime
import os
import json
from profanityfilter import ProfanityFilter

client = commands.Bot(command_prefix="-", intents=discord.Intents.all())
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
    await ctx.send(f"Ping: `{round(client.latency * 1000, 4)}ms`.")

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
            tagsl = msg.content.lower().split(", ")
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
        books.insert_one({"_id": b_id, "name": name, "author": ctx.author.id, "tags": tags, "date": date, "chapters": [], "namel": name.lower()})
        
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
        elif len(list(query)) == 1:
            book = books.find_one({"author": ctx.author.id})
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
            name = msg.content
            if chapters.find_one({"author": ctx.author.id, "namel": name.lower()}) != None:
                return await ctx.send("That chapter already exists lmao do -new again")

            chaps = book["chapters"]
            c_id = token_hex(5)
            chaps.append(c_id)
            books.update_one({"_id": book["_id"]}, {"$set": {"chapters": chaps}})
            chapters.insert_one({"_id": c_id, "name": name, "author": ctx.author.id, "book": book["_id"], "content": "(This chapter is empty)", "namel": name.lower()})

            e = discord.Embed(
                title="Your chapter has been created!",
                description="Use -write to add to this chapter",
                color=blue
            )
            
            e.set_footer(text=f"Note- if you want to keep your chapter content a secret, DM this bot with -add. Chapter ID: {c_id}")
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
    try:
        msg = await client.wait_for("message", timeout=40, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
    except TimeoutError:
        await err(ctx, "-add")
    else:
        cname = msg.content.lower()
        if chapters.find_one({"_id": cname}) == None:
            query = chapters.find({"namel": cname})
            if len(list(query)) == 0:
                await ctx.send("You don't have a chapter by that name-")
            elif len(list(query)) > 1:
                s = ""
                for q in query:
                    bname = books.find_one({"_id": q["book"]})["name"]
                    s += q["name"] + " from " + bname + " ID: " + q["book"] + "\n"
                await ctx.send(f"Did you mean:\n\n{s}\n\n(enter book ID)")
                try:
                    msg = await client.wait_for("message", timeout=20, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                except TimeoutError:
                    err(ctx, "-add")
                else:
                    b_id = msg.content.lower()
                    chapter = chapters.find_one({"book": b_id, "namel": cname})
                    if chapter == None:
                        return await ctx.send("That isn't a valid id lmao")
                    
                    chapter = chapter["_id"]
            else:
                chapter = chapters.find_one({"namel": cname})["_id"]
        else:
            chapter = cname
    
    await ctx.send("Do you wanna write from a text file (f) or from a message (m)? File is recommended for longer chapters.")
    try:
        msg = await client.wait_for("message", timeout=20, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
    except TimeoutError:
        await err(ctx, "-add")
    else:
        c = msg.content.lower()
        if c not in "fm":
            return await ctx.send("You didn't type f or m lmao do -add again")
        
        if c == "m":
            await ctx.send("Enter chapter content:")
            try:
                msg = await client.wait_for("message", timeout=120, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            except TimeoutError:
                await err(ctx, "-add")
            else:
                content = msg.content
        else:
            await ctx.send("Attach a .txt file with chapter content:")
            try:
                msg = await client.wait_for("message", timeout=40, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            except TimeoutError:
                await err(ctx, "-add")
            else:
                if len(msg.attachments) == 0:
                    return await ctx.send("You didn't attach any files-")
                
                fname = token_hex(8) + ".txt"
                await msg.attachments[0].save(fname)
                with open(fname) as f:
                    content = f.read()
                
                os.remove(fname)
        
        pf = ProfanityFilter()
        warn = ""
        if not pf.is_clean(content):
            content = ":warning: This story contains content that may not be suited towards younger audiences.\n\n" + content
            warn = "A swear word warning has been added."
        chapters.update_one({"_id": chapter}, {"$set": {"content": content}})

        await ctx.send("Added chapter content. " + warn)

'''
@client.command()
async def read(ctx):
    await ctx.send("Enter book/chapter name or ID")
    try:
        msg = await client.wait_for("message", timeout=40, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
    except TimeoutError:
        await err(ctx, "-read")
    else:
        search = msg.content.lower()
        
        if chapters.find_one({"_id": search}) == None:

        else:
            chapter = chapters.find_one({"_id": search})
            if chapter == None:
                chapter = chapters.find({"namel": search})
                if len(chapters) == 0:
                    book = books.find_one({"_id": search})
                    if book == None:
                        book = books.find({"name": search})
                        if len(books) == 0:
                            await ctx.send("Couldn't find a book or chapter by that name")\
                        else:
                            # chapters of book
                    else:
                        # chapters of book
                elif len(chapters) > 1:
            else:
                content = chapter["content"]
'''

@client.command()
async def read(ctx, c_id):
    chapter = chapters.find_one({"_id": c_id})
    e = discord.Embed(
        title=chapter["name"],
        description=chapter["content"],
        color=blue
    )
    e.set_footer(text=f"By {client.get_user(chapter['author']).name}")

    await ctx.send(embed=e)

@client.command(name="eval")
async def _eval(ctx, *, cmd):
    await ctx.send(eval(cmd))

@client.command(name="exec")
async def _exec(ctx, *, cmd):
    await ctx.send(exec(cmd))

client.run(tokens["bot"])
