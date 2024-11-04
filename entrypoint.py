import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='Bot Runner')
    parser.add_argument('--bot_script', required=True, help='Path to the bot script to execute')
    parser.add_argument('--run_id', required=True, help='Run ID for tracking')
    args, unknown = parser.parse_known_args()

    # Prepare the command to run the bot script
    bot_script = args.bot_script
    run_id = args.run_id
    bot_command = ['python3', bot_script, '--run_id', run_id] + unknown

    # Execute the bot script
    os.execvp('python3', bot_command)

if __name__ == '__main__':
    main()
