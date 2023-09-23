# implementation   
from Voicebox import Voicebox
import os
from dotenv import load_dotenv

def main():
    # implementation
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    voicebox = Voicebox(token)
    voicebox.start()

if __name__ == '__main__':
    main()