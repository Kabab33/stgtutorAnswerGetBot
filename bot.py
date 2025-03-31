print('Starting...')
from dotenv import load_dotenv
from os import getenv
from termcolor import colored
import discord
from discord.ext import commands
from json import loads
import requests
from re import sub
from re import compile
load_dotenv()

stgtoken = getenv('STUDYGO_TOKEN')
if stgtoken == None:
    print(colored('[ERROR] Studygo token not found', 'red'))
    print(colored('[ERROR] Please set the token in your .env and make shure it is called STUDYGO_TOKEN see .env.example for an example', 'red'))
    exit()
elif stgtoken == 'STUDYGO_TOKEN_HERE':
    print(colored('[ERROR] Studygo token not found', 'red'))
    print(colored('[ERROR] Please replace the temp token in your .env', 'red'))
    exit()
else:
    print(colored('[SUCSESS] Studygo token found', 'green'))
    partial_token = stgtoken[0:8] + '...' + stgtoken[-8:]
    print(colored(f'[INFO] Partial token: {partial_token}', 'blue'))


bot = commands.Bot()
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r, g, b

def removeHtmlTags(text):
    cleanr = compile('<.*?>')
    cleantext = sub(cleanr, ' ', text)
    cleantext = sub(' +', ' ', cleantext)
    cleantext = cleantext.strip()
    cleantext = cleantext.replace('\n', ' ')
    cleantext = cleantext.replace('\r', ' ')
    cleantext = cleantext.replace('\t', ' ')
    cleantext = cleantext.replace('  ', ' ')
    cleantext = cleantext.replace('&nbsp', ' ')
    return cleantext

def get_form_data(id:int, raw:bool=False):
    
    url = f'https://api.wrts.nl/api/v3/public/qna/questions/{id}'
    response = requests.get(url, headers={
    'X-Auth-Token': stgtoken
 })
    print(colored(f"[LOG] {url} is opgevraagd van studygo", 'blue'))
    print(colored(f"[LOG] studygo zei: {response.status_code} {response.reason}", 'blue'), flush=True)
    if response.status_code != 200:
        print(colored(f"[ERROR] {response.status_code} {response.reason}", 'red'), flush=True)
    if raw:
        return response
    else: 
        responce_details= {
            'status_code': response.status_code,
            'reason': response.reason,
            'success': response.status_code == 200,
            
        }
        dresponse = loads(response.text)
        tutanswr = []
        for answer in dresponse['qna_question']['tutor_qna_answers']:
            tutanswr.append({
                'body': removeHtmlTags(answer['body']),
                'tutor': {
                    'naam': answer['user']['first_name'],
                    'gebruikersnaam': answer['user']['username'],
                    'avatar': answer['user']['profile_image']['image_url'],
                    'kleur': answer['user']['profile_image']['profile_color'],
                },
                'attatchments': answer['qna_attachments']
            })
    return tutanswr, responce_details




@bot.slash_command(
    name="tutanswget",
    description="Pakt de antwoorden van de tutor en stopt ie in een embed",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    }
)
async def tutanswgett(ctx, url:discord.Option(discord.SlashCommandOptionType.string)):
    print(colored(f"[LOG] {ctx.author} heeft de url {url} opgevraagd", 'blue'), flush=True)
    spliturl = url.split('/')
    if len(spliturl) < 7:
        embed = discord.Embed(
            title="Ongeldige URL",
            description="De URL is ongeldig. Zorg ervoor dat de URL een geldige vraag bevat.",
            color=discord.Color.red()
        )
        await ctx.respond(embeds=[embed])
    elif spliturl[2] != 'studygo.com':
        embed = discord.Embed(
            title="Ongeldige URL",
            description="De URL is niet een studygo url.",
            color=discord.Color.red()
        )
        await ctx.respond(embeds=[embed])
    elif spliturl[3] != 'nl':
        embed = discord.Embed(
            title="Ongeldige URL",
            description="De URL is niet een nederlandse studygo url.",
            color=discord.Color.red()
        )
        await ctx.respond(embeds=[embed])
    elif spliturl[4] != 'learn' or spliturl[5] != 'question' or spliturl[6] == '':
        embed = discord.Embed(
            title="Ongeldige URL",
            description="De URL is niet een geldige vraag.",
            color=discord.Color.red()
        )
        await ctx.respond(embeds=[embed])
    #check of de url id alleen nummer bevat
    elif not spliturl[6].isnumeric():
        embed = discord.Embed(
            title="Ongeldige URL",
            description="De URL is niet een geldige vraag.",
            color=discord.Color.red()
        )
        await ctx.respond(embeds=[embed])
    else:
        id = int(spliturl[6])
        res, stat = get_form_data(id)
        #loop door de antwoorden en maak een embed voor elk antwoord
        embedss = []
        if stat['success'] == False:
            embed = discord.Embed(
                title="ERROR",
                description=f"Studygo RETEURND {stat['status_code']} NOT SUCSESS",
                footer=f"Reason: {stat['reason']}",
                color=discord.Color.red()
            )
        for answer in res:
            r, g, b = hex_to_rgb(answer['tutor']['kleur'])
            embed = discord.Embed(
                title=f"Antwoord van {answer['tutor']['naam']}",
                description=answer['body'],
                color=discord.Color.from_rgb(r, g, b)
            )
            embed.set_author(name=answer['tutor']['naam'], icon_url=answer['tutor']['avatar'], url=f"https://www.studygo.com/nl/learn/{answer['tutor']['gebruikersnaam']}")

            #check of de attatchment een image is
            if len(answer['attatchments']) > 0 and 'image' in answer['attatchments'][0]:
                image = answer['attatchments'][0]['image']
                embed.set_image(url=image)

            embedss.append(embed)
            if len(answer['attatchments']) > 0:
                for attatchment in answer['attatchments']:
                    #check of de attatchment  de image property heeft
                    if not 'image' in attatchment:
                        attatchmentEmbed = discord.Embed(
                            title='Attatchment',
                            description=str(attatchment),
                            footer='dit attatchment type is niet ondersteund contact de eigenaar van de bot',
                            color=discord.Color.blue()
                        )
                        embedss.append(attatchmentEmbed)
            
        if len(embedss) <= 0:
            embed = discord.Embed(
                title="Geen antwoorden gevonden",
                description="Er zijn geen antwoorden gevonden voor deze vraag.",
                color=discord.Color.red()
            )
            await ctx.respond(embeds=[embed])
        else:
            await ctx.respond(embeds=embedss)






@bot.slash_command(
    name="tutanswgetid",
    description="Pakt de antwoorden van de tutor en stopt ie in een embed",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    }
)
async def tutanswgettid(ctx, id:discord.Option(discord.SlashCommandOptionType.integer)):
    print(colored(f"[LOG] {ctx.author} heeft de id {id} opgevraagd", 'blue'), flush=True)
    res, sdat = get_form_data(id)
    #loop door de antwoorden en maak een embed voor elk antwoord
    if sdat['success'] == False:
            embed = discord.Embed(
                title="ERROR",
                description=f"Studygo RETEURND {sdat['status_code']} NOT SUCSESS",
                footer=f"Reason: {sdat['reason']}",
                color=discord.Color.red()
            )
    embedss = []
    for answer in res:
        r, g, b = hex_to_rgb(answer['tutor']['kleur'])
        embed = discord.Embed(
            title=f"Antwoord van {answer['tutor']['naam']}",
            description=answer['body'],
            color=discord.Color.from_rgb(r, g, b)
        )
        embed.set_author(name=answer['tutor']['naam'], icon_url=answer['tutor']['avatar'], url=f"https://www.studygo.com/nl/learn/{answer['tutor']['gebruikersnaam']}")

        #check of de attatchment een image is
        if len(answer['attatchments']) > 0 and 'image' in answer['attatchments'][0]:
            image = answer['attatchments'][0]['image']
            embed.set_image(url=image)

        embedss.append(embed)
        if len(answer['attatchments']) > 0:
            for attatchment in answer['attatchments']:
                #check of de attatchment  de image property heeft
                if not 'image' in attatchment:
                    attatchmentEmbed = discord.Embed(
                        title='Attatchment',
                        description=str(attatchment),
                        footer='dit attatchment type is niet ondersteund contact de eigenaar van de bot',
                        color=discord.Color.blue()
                    )
                    embedss.append(attatchmentEmbed)
            
    if len(embedss) <= 0:
        embed = discord.Embed(
            title="Geen antwoorden gevonden",
            description="Er zijn geen antwoorden gevonden voor deze vraag.",
            color=discord.Color.red()
        )
        await ctx.respond(embeds=[embed])
    else:
        await ctx.respond(embeds=embedss)



@bot.slash_command(
    name = "pong",
    description = "Ping!",
    integration_types={
        discord.IntegrationType.guild_install,
        discord.IntegrationType.user_install,
    },
)
async def say_hello(ctx):
    await ctx.respond("Ping!")


@bot.listen()
async def on_connect():
    await bot.sync_commands(force=True, delete_existing=True)
    print (colored('cmd synced', 'green'), flush=True)


dsctoken = getenv('DISCORD_TOKEN')

if dsctoken == None:
    
    print(colored('[ERROR] Discord token not found', 'red'))
    print(colored('[ERROR] Please set the token in your .env and make shure it is called DISCORD_TOKEN see .env.example for an example', 'red'))
    exit()
elif dsctoken == 'DISCORD_BOT_TOKEN_HERE':
    
    print(colored('[ERROR] Discord token not found', 'red'))
    print(colored('[ERROR] Please replace the temp token in your .env', 'red'))
    exit()
else:
    print(colored('[SUCSESS] discord token found', 'green'))
    partial_token = dsctoken[0:8] + '...' + dsctoken[-8:]
    print(colored(f'[INFO] Partial token: {partial_token}', 'blue'))
    print(colored('[SUCCESS] Bot is starting...', 'green'))
    bot.run(dsctoken)