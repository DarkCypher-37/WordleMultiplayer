import colorama                    # DEBUG

R = 'red'
G = 'green'
Y = 'yellow'
B = 'black'

colorama.init()
green = colorama.Fore.GREEN
red = colorama.Fore.RED
yellow = colorama.Fore.YELLOW
reset = colorama.Style.RESET_ALL

def cprint(color, msg):
    if color == R:
        print(f"{red}{msg}{reset}")
    elif color == G:
        print(f"{green}{msg}{reset}")
    elif color == Y:
        print(f"{yellow}{msg}{reset}")
    elif color == B:
        print(msg)