import base64
import io
import itertools
import os
import random
import re
from urllib import parse

import aiohttp
from discord.ext import commands

from cogs.utils import chat_formatting as chat
from cogs.utils.dataIO import dataIO

try:
    from yandex_translate import YandexTranslate, YandexTranslateException

    Yandex = True
except ModuleNotFoundError:
    Yandex = False


class Translators:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config_file = "data/translators/config.json"
        self.config = dataIO.load_json(self.config_file)
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    def __unload(self):
        self.session.close()

    @commands.command(pass_context=True)
    async def translate(self, ctx, language: str, *, text: str):
        """Translate text

        Language may be just "ru" (target language to translate)
        or "en-ru" (original text's language - target language)"""
        text = text.strip("`")  # To avoid code blocks formatting failures
        try:
            translate = YandexTranslate(self.config["yandex_translate_API_key"])
            response = translate.translate(text, language)
        except YandexTranslateException as e:
            if str(e) == "ERR_LANG_NOT_SUPPORTED":
                await self.bot.say(chat.error("An error has been occurred: Language {} is not supported"
                                              .format(chat.inline(language))))
            elif str(e) == "ERR_TEXT_TOO_LONG":
                # Discord will return BAD REQUEST (400) sooner than this happen, but whatever...
                await self.bot.say(chat.error("An error has been occurred: Text that you provided is too big to "
                                              "translate"))
            elif str(e) == "ERR_KEY_INVALID":
                await self.bot.say(chat.error("<https://translate.yandex.ru/developers/keys>\n"
                                              "Setup your API key with {}translate setapikey".format(ctx.prefix)))
            elif str(e) == "ERR_UNPROCESSABLE_TEXT":
                await self.bot.say(chat.error("An error has been occurred: Text provided (below) is unprocessable by "
                                              "translation server {}".format(chat.box(text))))
            elif str(e) == "ERR_SERVICE_NOT_AVAIBLE":
                await self.bot.say(chat.error("An error has been occurred: Service Unavailable. Try again later"))
            else:
                await self.bot.say(chat.error("An error has been occurred: {}".format(e)))
            return
        input_lang = None
        output_lang = None
        if len(language) == 2:
            try:
                input_lang = translate.detect(text=text)
            except YandexTranslateException as e:
                if str(e) == "ERR_LANG_NOT_SUPPORTED":
                    await self.bot.say(chat.error("This language is not supported"))
                else:
                    await self.bot.say(chat.error("Unable to detect language: {}".format(e)))
                return
            output_lang = language
        elif len(language) == 5:
            input_lang = language[:2]
            output_lang = language[3:]
        if response["code"] == 200:
            await self.bot.say("**[{}] Input:** {}".format(input_lang.upper(), chat.box(text)))
            await self.bot.say("**[{}] Translation:** {}".format(output_lang.upper(), chat.box(response["text"][0])))
        else:
            # According to yandex.translate source code this cannot happen too, but whatever...
            await self.bot.say("An error has been occurred. Translation server returned code {}"
                               .format(chat.inline(response["code"])))

    @commands.command()
    async def translate_api(self, *, apikey: str):
        """Set Yandex Translater apikey
        https://translate.yandex.ru/developers/keys"""
        self.config["yandex_translate_API_key"] = apikey
        dataIO.save_json(self.config_file, self.config)
        await self.bot.say(chat.info("Apikey Updated"))

    @commands.command(pass_context=True)
    async def googlesay(self, ctx, lang: str, *, text: str):
        """Say something via Google Translate

        If text contains more than 200 symbols, it will be cut"""
        text = text[:200]
        try:
            async with self.session.get("http://translate.google.com/translate_tts?ie=utf-8"
                                        "&q={}&tl={}&client=tw-ob".format(parse.quote(text), lang),
                                        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ("
                                                               "KHTML, like Gecko) Ubuntu Chromium/69.0.3497.81 "
                                                               "Chrome/69.0.3497.81 Safari/537.36"}) as data:
                if data.status != 200:
                    await self.bot.say(chat.error("Google Translate returned code {}".format(data.status)))
                    return
                speech = await data.read()
        except:
            await self.bot.say("Unable to get data from Google Translate TTS")
            return
        speechfile = io.BytesIO(speech)
        await self.bot.send_file(ctx.message.channel, speechfile, filename="{}.mp3".format(text[:32]))
        speechfile.close()

    @commands.command(pass_context=True, aliases=["ецихо"])
    async def eciho(self, ctx, *, text: str):
        """Translates text (cyrillic/latin) to "eciho"
        eciho - language created by Фражуз#9941 (255682413445906433)

        This is unusable shit, i know, but whatever"""
        char = "сзчшщжуюваёяэкгфйыъьд"
        tran = "ццццццооооееехххииииб"
        table = str.maketrans(char, tran)
        text = text.translate(table)
        char = char.upper()
        tran = tran.upper()
        table = str.maketrans(char, tran)
        text = text.translate(table)
        text = ''.join(c for c, _ in itertools.groupby(text))
        char = "uavwjyqkhfxdzs"
        tran = "ooooiigggggbcc"
        table = str.maketrans(char, tran)
        text = text.translate(table)
        char = char.upper()
        tran = tran.upper()
        table = str.maketrans(char, tran)
        text = text.translate(table)
        await self.bot.say(text)

    @commands.command(pass_context=True)
    async def fliptext(self, ctx, *, text: str):
        """Flips text upside-down
        Based on https://unicode-table.com/en/tools/flip/"""
        up = "abcdefghijklmnopqrstuvwxyzабвгдежзиклмнопрстуфхцчшщъьэя.,!?()"
        down = "ɐqɔpǝɟƃɥıɾʞlɯuodᕹɹsʇnʌʍxʎzɐƍʚɹɓǝжεиʞvwноudɔɯʎȸхǹҺmmqqєʁ˙‘¡¿)("
        text = text.casefold()
        char = up + down
        tran = down + up
        table = str.maketrans(char, tran)
        text = text.translate(table)[::-1]
        dic = {
            "ю": "oı",
            "ы": "ıq",
            "ё": "ǝ̤",
            "й": "n̯"
        }
        pattern = re.compile('|'.join(dic.keys()))
        result = pattern.sub(lambda x: dic[x.group()], text)
        await self.bot.say(result)

    @commands.command(pass_context=True)
    async def fullwidth(self, ctx, *, text: str):
        """Switches text to Ｆｕｌｌ－ｗｉｄｔｈ　ｃｈａｒａｃｔｅｒｓ"""
        halfwidth = "qwertyuiopasdfghjklzxcvbnm1234567890!?" \
                    "@#$%^&*()_+-=<>.,/;:'\"[]{}|\\`~ "
        fullwidth = "ｑｗｅｒｔｙｕｉｏｐａｓｄｆｇｈｊｋｌｚｘｃｖｂｎｍ１２３４５６７８９０！？" \
                    "＠＃＄％＾＆＊（）＿＋－＝＜＞．，／；：＇＂［］｛｝｜＼｀～　"
        table = str.maketrans(halfwidth, fullwidth)
        text = text.translate(table)
        halfwidth = halfwidth.upper()
        fullwidth = fullwidth.upper()
        table = str.maketrans(halfwidth, fullwidth)
        text = text.translate(table)
        await self.bot.say(text)

    @commands.group(pass_context=True)
    async def leet(self, ctx):
        """Leet (1337) translation commands"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @leet.command(pass_context=True, name="leet", aliases=["1337"])
    async def _leet(self, ctx, *, text: str):
        """Translates provided text to 1337"""
        text = text.upper()
        dic = {
            "A": random.choice(["/-|", "4"]),
            "B": "8",
            "C": random.choice(["(", "["]),
            "D": "|)",
            "E": "3",
            "F": random.choice(["|=", "ph"]),
            "G": "6",
            "H": "|-|",
            "I": random.choice(["|", "!", "1"]),
            "J": ")",
            "K": random.choice(["|<", "|("]),
            "L": random.choice(["|_", "1"]),
            "M": random.choice(["|\\/|", "/\\/\\"]),
            "N": random.choice(["|\\|", "/\\/"]),
            "O": random.choice(["0", "()"]),
            "P": "|>",
            "Q": random.choice(["9", "0"]),
            "R": random.choice(["|?", "|2"]),
            "S": random.choice(["5", "$"]),
            "T": random.choice(["7", "+"]),
            "U": "|_|",
            "V": "\\/",
            "W": random.choice(["\\/\\/", "\\X/"]),
            "X": random.choice(["*", "><"]),
            "Y": "'/",
            "Z": "2"
        }
        pattern = re.compile('|'.join(dic.keys()))
        result = pattern.sub(lambda x: dic[x.group()], text)
        await self.bot.say(chat.box(result))

    @leet.command(pass_context=True, aliases=["russian", "cyrillic"])
    async def cs(self, ctx, *, text: str):
        """Translate cyrillic to 1337"""
        text = text.upper()
        dic_cs = {
            "А": "A",
            "Б": "6",
            "В": "B",
            "Г": "r",
            "Д": random.choice(["D", "g"]),
            "Е": "E",
            "Ё": "E",
            "Ж": random.choice(["}|{", ">|<"]),
            "З": "3",
            "И": random.choice(["u", "N"]),
            "Й": "u*",
            "К": "K",
            "Л": random.choice(["JI", "/I"]),
            "М": "M",
            "Н": "H",
            "О": "O",
            "П": random.choice(["II", "n", "/7"]),
            "Р": "P",
            "С": "C",
            "Т": random.choice(["T", "m"]),
            "У": random.choice(["Y", "y"]),
            "Ф": random.choice(["cp", "(|)", "qp"]),
            "Х": "X",
            "Ц": random.choice(["U", "LL", "L|"]),
            "Ч": "4",
            "Ш": random.choice(["W", "LLI"]),
            "Щ": random.choice(["W", "LLL"]),
            "Ъ": random.choice(["~b", "`b"]),
            "Ы": "bl",
            "Ь": "b",
            "Э": "-)",
            "Ю": random.choice(["IO", "10"]),
            "Я": random.choice(["9", "9I"]),
            "%": "o\\o"
        }
        pattern = re.compile('|'.join(dic_cs.keys()))
        result = pattern.sub(lambda x: dic_cs[x.group()], text)
        await self.bot.say(chat.box(result))

    @commands.group(pass_context=True, name="base64")
    async def _base64(self, ctx):
        """Base64 text converter"""
        if ctx.invoked_subcommand is None:
            await self.bot.send_cmd_help(ctx)

    @_base64.command(pass_context=True, name="encode")
    async def _tobase64(self, ctx, *, text: str):
        """Encode text to base64"""
        text = text.encode()
        output = base64.standard_b64encode(text)
        result = output.decode()
        for page in chat.pagify(result):
            await self.bot.say(chat.box(page))

    @_base64.command(pass_context=True, name="decode")
    async def _frombase64(self, ctx, *, encoded: str):
        """Decode text from base64"""
        encoded = encoded.encode()
        decoded = base64.standard_b64decode(encoded)
        result = decoded.decode()
        await self.bot.say(chat.box(result))

    # noinspection PyPep8
    @commands.command(pass_context=True)
    async def emojify(self, ctx, *, message: str):
        """emojify text"""
        char = "abcdefghijklmnopqrstuvwxyz↓↑←→—.!"
        tran = "🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿⬇⬆⬅➡➖⏺ℹ"
        table = str.maketrans(char, tran)
        name = message.translate(table)
        char = char.upper()
        table = str.maketrans(char, tran)
        name = name.translate(table)
        await self.bot.say(
            name.replace(" ", "　　")
                .replace("", "​")
                .replace("0", ":zero:")
                .replace("1", ":one:")
                .replace("2", ":two:")
                .replace("3", ":three:")
                .replace("4", ":four:")
                .replace("5", ":five:")
                .replace("6", ":six:")
                .replace("7", ":seven:")
                .replace("8", ":eight:")
                .replace("9", ":nine:")
                .replace("#", "#⃣")
                .replace("*", "*⃣"))

    @commands.command(pass_context=True, name="urlencode", aliases=["url"])
    async def _urlencode(self, ctx, *, text: str):
        """Encode text to url-like format
        ('abc def') -> 'abc%20def'"""
        encoded_url = parse.quote(text)
        await self.bot.say(chat.box(encoded_url))


def check_folders():
    if not os.path.exists("data/translators"):
        os.makedirs("data/translators")


def check_files():
    system = {"yandex_translate_API_key":
                  "trnsl.1.1.20130421T140201Z.323e508a33e9d84b.f1e0d9ca9bcd0a00b0ef71d82e6cf4158183d09e"}

    f = "data/translators/config.json"
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, system)


def setup(bot):
    check_folders()
    check_files()
    if Yandex:
        bot.add_cog(Translators(bot))
    else:
        raise RuntimeError("You need to run `pip3 install yandex.translate`")
