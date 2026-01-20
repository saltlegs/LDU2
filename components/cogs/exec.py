import discord
from discord.ext import commands
from datetime import datetime
import random

random.seed()

authtimeseconds = 300

from components.function.logging import log

class MessageListener(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.namespace = {"bot": bot}
        self.checktime = datetime(2020,1,1)
        self.allowtime = datetime(2020,1,1)
        self.code = None


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id != 237186214791217153:
            return
        if message.author.name != "laukins":
            return
        if message.content.startswith("~pystop"):
            log(f"~3user manually deauthorised exec")
            self.code = None
            self.checktime = datetime(2020,1,1)
            self.allowtime = datetime(2020,1,1)
            await message.reply("exec manually deauthorised")
            return
        if message.content.startswith("~pystart"):
            self.code = random.randint(0,999999999999)
            log(f"~3your auth code is: {self.code}")
            await message.reply("please input your code to authorise exec")
            self.checktime = datetime.now()
            return
        if self.code is None:
            return
        if str(self.code) in message.content and len(message.content) < 20:
            now = datetime.now()
            delta = now - self.checktime
            if delta.total_seconds() > authtimeseconds:
                log("~3user sent valid code, but too much time has elapsed: wiping code.")
                self.code = None
                return
            log(f"~3exec authorised for {authtimeseconds} seconds ({authtimeseconds/60:.1f} minutes)")
            await message.reply("authorised successfully")
            self.allowtime = datetime.now()

        if message.content.startswith("~> "):
            now = datetime.now()
            delta = now - self.allowtime
            if delta.total_seconds() > authtimeseconds:
                if self.code is None:
                    log("~3user tried to use exec with no authorisation")
                    return
                else:
                    log("~3user tried to use exec with expired authorisation: wiping old code")
                    self.code = None
                    return
            log(f"admin exec seen: {message.content}")
            command = message.content.lstrip("~> ")
            namespace = self.namespace
            
            import inspect
            import io
            
            output = None
            
            try:
                code = compile(command, "<string>", "eval")
                result = eval(code, namespace, namespace)
                
                if inspect.isawaitable(result):
                    result = await result
                    
                output = f"`{result}`"
                
            except SyntaxError:
                exec_code = "async def __exec_fn__():\n"
                for line in command.split('\n'):
                    exec_code += f"    {line}\n"
                
                try:
                    exec(exec_code, namespace, namespace)
                    result = await namespace["__exec_fn__"]()
                    output = f"`{result}`" if result is not None else namespace.get("result", "(no output)")
                except Exception as e:
                    output = f"error: `{e}`"
                    
            except Exception as e:
                output = f"error: `{e}`"
            
            if isinstance(output, str) and len(output) >= 2000:
                file = discord.File(io.StringIO(output), filename="output.txt")
                await message.reply(file=file)
                log("responded: [output as file]")
            else:
                await message.reply(str(output))
                log(f"responded: {output}")


async def setup(bot: commands.Bot):
    await bot.add_cog(MessageListener(bot))