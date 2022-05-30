import colorama                    # DEBUG

R = 'red'
G = 'green'
Y = 'yellow'
B = 'black'
C = 'cyan'
M = 'magenta'

colorama.init()
green = colorama.Fore.GREEN
red = colorama.Fore.RED
yellow = colorama.Fore.YELLOW
cyan = colorama.Fore.CYAN
magenta = colorama.Fore.MAGENTA
reset = colorama.Style.RESET_ALL

def cprint(color, msg):
    if color == R:
        print(f"{red}{msg}{reset}")
    if color == M:
        print(f"{magenta}{msg}{reset}")
    elif color == G:
        print(f"{green}{msg}{reset}")
    elif color == Y:
        print(f"{yellow}{msg}{reset}")
    elif color == C:
        print(f"{cyan}{msg}{reset}")
    elif color == B:
        print(msg)