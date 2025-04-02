import discord  # From discord.py-self
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
TOKEN = os.getenv("DISCORD_USER_TOKEN")  # Get token from .env file
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "0"))  # Get guild ID from .env file
OUTPUT_DIR = os.getenv(
    "OUTPUT_DIR", "obsidian_notes"
)  # Get output directory from .env file

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)


print("Starting")


class MemberExtractor(discord.Client):
    def __init__(self):
        print("Initializing client...")
        # For older discord.py versions, we don't need to set intents
        super().__init__()

    async def on_connect(self):
        print("Connected to Discord!")

    async def on_error(self, event, *args, **kwargs):
        print(f"Error in {event}:")
        import traceback

        traceback.print_exc()

    async def on_ready(self):
        print(f"Logged in as {self.user.name} ({self.user.id})")

        try:
            # Get the guild
            guild = self.get_guild(GUILD_ID)
            if not guild:
                print(f"Could not find guild with ID {GUILD_ID}")
                await self.close()
                return

            print(f"Processing members from {guild.name} (Guild ID: {guild.id})")

            # Use specific channel ID
            channel_id = 1355211248131641506
            channel = guild.get_channel(channel_id)

            if not channel:
                print(f"Could not find channel with ID {channel_id}")
                await self.close()
                return

            print(
                f"Using channel #{channel.name} (Channel ID: {channel.id}) for member scraping"
            )
            print(f"Channel type: {type(channel).__name__}")
            print(
                f"Can read messages: {channel.permissions_for(guild.me).read_messages}"
            )
            print(f"Can view channel: {channel.permissions_for(guild.me).view_channel}")

            # Fetch all members using the specified channel
            print("Starting member fetch...")
            members = []
            try:
                async for member in guild.fetch_members(channels=[channel]):
                    print(f"Found member: {member.name}")
                    # Check if you have DMs with this member
                    has_dm = False
                    try:
                        dm_channel = await member.create_dm()
                        async for _ in dm_channel.history(limit=1):
                            has_dm = True
                            break
                    except:
                        pass

                    # Store member info
                    member_info = {
                        "username": member.name,
                        "display_name": member.display_name,
                        "discord_id": member.id,
                        "roles": [
                            role.name
                            for role in member.roles
                            if role.name != "@everyone"
                        ],
                        "joined_at": (
                            str(member.joined_at) if member.joined_at else "Unknown"
                        ),
                        "avatar_url": (
                            str(member.avatar.url) if member.avatar else "No avatar"
                        ),
                        "has_dm": has_dm,
                    }
                    members.append(member_info)

                    # Display member info and prompt for action
                    print("\n" + "=" * 50)
                    print(f"Username: {member_info['username']}")
                    print(f"Display Name: {member_info['display_name']}")
                    print(f"Discord ID: {member_info['discord_id']}")
                    print(f"Roles: {', '.join(member_info['roles'])}")
                    print(f"Joined At: {member_info['joined_at']}")
                    print(f"Avatar URL: {member_info['avatar_url']}")
                    print(
                        f"Has DM with you: {'Yes' if member_info['has_dm'] else 'No'}"
                    )

                    create_file = (
                        input("Generate markdown file for this member? (y/n): ")
                        .strip()
                        .lower()
                    )
                    if create_file == "y":
                        filename = f"{member_info['username']}.md"
                        filepath = os.path.join(OUTPUT_DIR, filename)

                        # Create markdown file with YAML frontmatter
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write("---\n")
                            f.write(f"discord_username: {member_info['username']}\n")
                            f.write(f"discord_id: {member_info['discord_id']}\n")
                            f.write("---\n")

                        print(f"Created file: {filepath}")
            except Exception as e:
                print(f"Error during member fetch: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                raise  # Re-raise to see full traceback

            # Create an index file
            created_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".md")]
            if created_files:
                index_path = os.path.join(OUTPUT_DIR, "discord_members_index.md")
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write("# Discord Members Index\n\n")
                    f.write(
                        "Generated on "
                        + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        + "\n\n"
                    )

                    for file in created_files:
                        member_name = file[:-3]  # Remove .md extension
                        f.write(f"- [[{member_name}]]\n")

                print(f"\nCreated index file: {index_path}")

            print("\nDone!")

        except Exception as e:
            print(f"Error: {e}")

        await self.close()


# Run the client
print("Creating client instance...")
client = MemberExtractor()
print("Client instance created, attempting to run...")
try:
    # Ensure TOKEN is a string before running
    if TOKEN is None:
        raise ValueError("DISCORD_USER_TOKEN not found in environment variables")
    print(f"Token length: {len(TOKEN)}")  # Don't print the actual token!
    client.run(TOKEN)
except Exception as e:
    print(f"Failed to start client: {type(e).__name__}: {str(e)}")
    raise
