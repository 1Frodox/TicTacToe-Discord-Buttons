import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands
import asyncio
import time

class TictacToeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.challenges = {}  # Stores data for each challenge
        self.timeout_task = None  # Stores the timeout task

    @app_commands.command(name="tictactoe", description="Challenge another player to a Tic-Tac-Toe game")
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.User):
        if interaction.user == opponent:
            return await interaction.response.send_message("**[**You cannot challenge yourself.**]**", ephemeral=True)

        challenger = interaction.user
        eta_timestamp = int(time.time()) + 31  # Challenge expiration timestamp

        accept_button = Button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept")
        view = View()
        view.add_item(accept_button)

        challenge_message = await interaction.response.send_message(
            f"{opponent.mention}, you have been challenged to **TicTacToe**!\nThe challenge will expire <t:{eta_timestamp}:R>.",
            view=view
        )
        msg = await interaction.original_response()

        self.challenges[msg.id] = {
            "challenger": challenger,
            "opponent": opponent,
            "accepted": False,
            "message": msg,
        }
        asyncio.create_task(self.delete_challenge_message(msg.id, 30))  # 30 seconds timeout for the challenge

        async def accept_button_callback(interaction: discord.Interaction):
            if interaction.user == opponent:
                self.challenges[msg.id]["accepted"] = True
                accept_button.disabled = True
                await msg.edit(content=f"**[**{opponent.mention} has accepted the challenge.**]**", view=view)
                await interaction.response.defer()

                players = [challenger, opponent]
                current_player = 0
                board = [None] * 9
                game_data = {'players': players, 'current_player': current_player, 'board': board}

                # Create TicTacToe buttons
                buttons = [Button(label="-", row=i//3, style=discord.ButtonStyle.grey, custom_id=str(i)) for i in range(9)]
                game_view = View()
                for button in buttons:
                    game_view.add_item(button)

                # Send the game setup message
                game_message = await interaction.followup.send(
                    content=f"**Tictactoe [**{opponent.display_name} vs {challenger.display_name}**]**\nTurn: {players[current_player].mention}",
                    view=game_view
                )

                # Check for a winning combination
                def check_win(board, symbol):
                    winning_combinations = [
                        [0, 1, 2], [3, 4, 5], [6, 7, 8],
                        [0, 3, 6], [1, 4, 7], [2, 5, 8],
                        [0, 4, 8], [2, 4, 6]
                    ]
                    return any(all(board[i] == symbol for i in combo) for combo in winning_combinations)

                # Handle player timeout
                async def player_timeout():
                    try:
                        await asyncio.sleep(30)
                        for button in game_view.children:
                            button.disabled = True
                        await game_message.edit(
                            content=f"**Tictactoe [**{opponent.display_name} vs {challenger.display_name}**]**\nCancelled.",
                            view=game_view
                        )
                    except asyncio.CancelledError:
                        pass

                # Handle button clicks in the game
                async def button_callback(interaction: discord.Interaction, button_index: int):
                    await interaction.response.defer()
                    nonlocal game_data, game_message

                    current_player = game_data['current_player']
                    players = game_data['players']
                    board = game_data['board']

                    if board[button_index] is not None or interaction.user != players[current_player]:
                        return

                    if self.timeout_task and not self.timeout_task.done():
                        self.timeout_task.cancel()

                    symbol = "X" if current_player == 0 else "O"
                    color = discord.ButtonStyle.red if current_player == 0 else discord.ButtonStyle.blurple

                    button = game_view.children[button_index]
                    button.style = color
                    button.label = symbol
                    board[button_index] = symbol

                    if check_win(board, symbol):
                        for button in game_view.children:
                            button.disabled = True
                        await game_message.edit(
                            content=f"**Tictactoe [**{opponent.display_name} vs {challenger.display_name}**]**\n{players[current_player].mention} has **won!**",
                            view=game_view
                        )
                        return

                    if all(cell is not None for cell in board):
                        for button in game_view.children:
                            button.disabled = True
                        await game_message.edit(
                            content=f"**Tictactoe [**{opponent.display_name} vs {challenger.display_name}**]**\n**Draw!**",
                            view=game_view
                        )
                        return

                    game_data['current_player'] = 1 - current_player  # Switch turn
                    self.timeout_task = asyncio.create_task(player_timeout())
                    await game_message.edit(
                        content=f"**Tictactoe [**{opponent.display_name} vs {challenger.display_name}**]**\nTurn: {players[game_data['current_player']].mention}",
                        view=game_view
                    )

                for i, button in enumerate(buttons):
                    button.callback = lambda interaction, i=i: button_callback(interaction, i)

                self.timeout_task = asyncio.create_task(player_timeout())
            else:
                await interaction.response.send_message(f"**[**You are not part of this game.**]**", ephemeral=True)

        accept_button.callback = accept_button_callback

    async def delete_challenge_message(self, message_id, delay):
        await asyncio.sleep(delay)
        if message_id in self.challenges and not self.challenges[message_id]["accepted"]:
            try:
                message = self.challenges[message_id]["message"]
                if message:
                    await message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            finally:
                del self.challenges[message_id]

async def setup(bot):
    await bot.add_cog(TictacToeCog(bot))
