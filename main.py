# implementation   
from Voicebox import Voicebox
import os

def main():
    # implementation
    token = os.getenv('DISCORD_BOT_TOKEN')
    voicebox = Voicebox(token)
    voicebox.start()

if __name__ == '__main__':
    main()