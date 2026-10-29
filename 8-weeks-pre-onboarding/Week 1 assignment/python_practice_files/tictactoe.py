import random
def displayBoard(playboard):
    print("")
    for i in range(len(playboard[0])):
        print("|", end="")
        for j in range(len(playboard[0])):
            print(f"{playboard[i][j]}", end="|")
        print("")


def playOption(playboard, playerChoice, player, options):
    if playerChoice not in options:
        print("choose option from the available options {}".format(displayOptions(options)))
        return True

    match playerChoice:
        case 1:
            playboard[0][0] = player
        case 2:
            playboard[0][1] = player
        case 3:
            playboard[0][2] = player
        case 4:
            playboard[1][0] = player
        case 5:
            playboard[1][1] = player
        case 6:
            playboard[1][2] = player
        case 7:
            playboard[2][0] = player
        case 8:
            playboard[2][1] = player
        case 9:
            playboard[2][2] = player
    index_option = options.index(playerChoice)
    options.pop(index_option)
    return False
        
def displayOptions(options):
    print("options : ", end="")
    for i in options:
        print(i, " ", end = "")
    

def checkWinner(playboard, players,winner):
    if (
       playboard[0][0] == playboard[0][1] == playboard[0][2] == players 
    or playboard[1][0] == playboard[1][1] == playboard[1][2] == players
    or playboard[2][0] == playboard[2][1] == playboard[2][2] == players
    or playboard[0][0] == playboard[1][1] == playboard[2][2] == players #diagonal
    or playboard[0][0] == playboard[1][0] == playboard[2][0] == players
    or playboard[0][1] == playboard[1][1] == playboard[2][1] == players
    or playboard[0][2] == playboard[1][2] == playboard[2][2] == players
    ):
        displayBoard(playboard)
        return players,True
    return None,False


def ChangecurrentPlayer(players ,currentPlayer):
    if currentPlayer == players[0]:
        return players[1]
    else:
        return players[0]

def computerOption(options):
    return random.choice(options)

dissatisfiedOption = True
playwithComputer = False
playingChoice = int(input("enter 1 to play with computer \nenter 2 to play with friend : "))
players = ["X", "O"]
options = [1,2,3,4,5,6,7,8,9]
playBoard = [
    ["_","_","_"],
    ["_","_","_"],
    ["_","_","_"],
]
total_choices = 9
choosePlaying=0
if playingChoice==1:
    choosePlaying = int(input("enter '1' for 'X'\nenter '2' for 'O' : "))
currentPlayer = players[choosePlaying-1]
winner = False

while total_choices!=0 and winner==False:
    while dissatisfiedOption:
        try:
            displayBoard(playBoard)
            if playingChoice==1 and currentPlayer!=players[choosePlaying-1]:
                dissatisfiedOption = playOption(playBoard, 
                                                computerOption(options), 
                                                currentPlayer, 
                                                options)
                continue
            print(f"\n{currentPlayer} turn choose from - ", end="")
            displayOptions(options)
            playerChoice = int(input("\nenter the option : "))
        except ValueError:
            print("--Input Error--Not a valid input - : enter from options only")
            continue
        dissatisfiedOption = playOption(playBoard, playerChoice, currentPlayer, options)

    gamewinner,winner = checkWinner(playBoard, currentPlayer,winner)
    if gamewinner==players[0]:
        print(f"winner is {players[0]}")
        break
    if gamewinner==players[1]:
            print(f"winner is {players[1]}")
            break
    currentPlayer = ChangecurrentPlayer(players, currentPlayer)
    total_choices-=1
    dissatisfiedOption = True


if winner==False and total_choices==0:
    displayBoard(playBoard)
    print("It's a Draw")

