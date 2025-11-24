import os, sys
from shutil import copyfile
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

PATH_SSH = os.path.dirname(__file__) # path to ssh folder
LOCK_FILENAME = PATH_SSH + '/active_profile.lock'
KEY_NAME = 'id_ed25519'

if not os.geteuid() == 0:
    sys.exit("\nWARNING: Only root can run this script\n")

# Parse command line arguments
parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-p", "--profile", default="auto", help="Profiles avaliables: santander or personal")
args = vars(parser.parse_args())

# Set up parameters
profile = args["profile"]

# print('script starting!')

def changeProfile():
    
    if(profile == "personal" or profile == "santander"):
        copyKeys(profile)
    elif(profile == "auto"):
        lock_profile = lockControl()
        copyKeys(lock_profile)
    else:
        print('Profile not found')

def copyKeys(profile):
    # TO-DO - Folder names automatically
    folder = "pessoal" if profile == 'personal' else "toro"
    copyfile( f'{PATH_SSH}/{folder}/{KEY_NAME}', f'{PATH_SSH}/{KEY_NAME}' )
    copyfile( f'{PATH_SSH}/{folder}/{KEY_NAME}.pub', f'{PATH_SSH}/{KEY_NAME}.pub')
    print(f'Active profile: {profile}')

# Check if the lock file exists and return the profile
def lockControl():
    if(os.path.exists(LOCK_FILENAME)):
        os.remove(LOCK_FILENAME)
        return 'santander'
    else:
        with open(LOCK_FILENAME, 'w') as f:
            f.write('personal')
        return 'personal'

def main():
    changeProfile()


if __name__ == "__main__":
    main()
