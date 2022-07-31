import mfrc522 as MFRC522
import RPi.GPIO as GPIO
import threading
import sqlite3
import random
import signal
import time
import os

# PREP SITE DB FOR TIC TAC TOE
dbase = sqlite3.connect('db.sqlite3')
cur = dbase.cursor()
cur.execute("UPDATE polls_cord SET XyCords='02' WHERE PieceId='X1'")
cur.execute("UPDATE polls_cord SET XyCords='21' WHERE PieceId='X2'")
cur.execute("UPDATE polls_cord SET XyCords='22' WHERE PieceId='X3'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X4'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X5'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X6'")
cur.execute("UPDATE polls_cord SET XyCords='11' WHERE PieceId='O1'")
cur.execute("UPDATE polls_cord SET XyCords='20' WHERE PieceId='O2'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='Enemy'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='W1'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='W2'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='W3'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='W4'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='W5'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='51'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='83'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='99'")
cur.execute("UPDATE polls_cord SET XyCords='y' WHERE PieceId='pieceS'")
dbase.commit()
dbase.close()

# ADDRESS CYCLE
none = [0, 0, 0, 0 ,0]
spaces = ['00', '01', '02', '10', '11', '12', '20', '21', '22']
fixed = ['02', '11', '20', '21', '22']
board_state = [tuple((0, none)),tuple((1, none)),tuple((2, none)),tuple((3, none)),
               tuple((4, none)),tuple((5, none)),tuple((6, none)),tuple((7, none)),
               tuple((8, none))]

#           0 2 6 8 9 10  14
#                       11  15
S3_cycle = [0,0,0,1,1,1,1,1,1]
S2_cycle = [0,0,1,0,0,0,0,1,1]
S1_cycle = [0,1,1,0,0,1,1,1,1]
S0_cycle = [0,0,0,0,1,0,1,0,1]
    
def state_for_computer(state):
    chains = []
    chains_of_3 = []
    chains_of_2 = []
    chain0 = [item for item in state if item[0] == '00' or item[0] == '01' or item[0] == '02']
    chain1 = [item for item in state if item[0] == '10' or item[0] == '11' or item[0] == '12']
    chain2 = [item for item in state if item[0] == '20' or item[0] == '21' or item[0] == '22']
    chain3 = [item for item in state if item[0] == '00' or item[0] == '10' or item[0] == '20']
    chain4 = [item for item in state if item[0] == '01' or item[0] == '11' or item[0] == '21']
    chain5 = [item for item in state if item[0] == '02' or item[0] == '12' or item[0] == '22']
    chain6 = [item for item in state if item[0] == '00' or item[0] == '11' or item[0] == '22']
    chain7 = [item for item in state if item[0] == '20' or item[0] == '11' or item[0] == '02']
    chains.extend((chain0, chain1, chain2, chain3, chain4, chain5, chain6, chain7))
    for chain in chains:
        if len(chain) == 3:
            if chain[0][1] == chain[1][1] and chain[0][1] == chain[2][1]:
                chains_of_3.append(chain)
        elif len(chain) == 2:
            if chain[0][1] == chain [1][1]:
                chains_of_2.append(chain)
    return chains_of_3, chains_of_2

def imagine_X(cord, current_state):
    current_state.append(tuple((cord, 'X')))
    imaginary_state = sorted(current_state)
    return state_for_computer(imaginary_state)

def comp_move(state, num_moves):
    dbase = sqlite3.connect('db.sqlite3')
    cur = dbase.cursor()
    query = "SELECT * FROM polls_cord WHERE XyCords != 'none' AND XyCords != 'n' AND XyCords != 'y'"
    occupied = []
    occupied_ref = []
    for row in cur.execute(query):
        occupied.append(row[4])
        occupied_ref.append(tuple((row[4], row[3])))
    unoccupied = sorted(set(occupied) ^ set(spaces))
    query = "SELECT * FROM polls_cord WHERE PieceId = 'pieceS'"
    for row in cur.execute(query):
        if row[4] == 'n' or num_moves > 2:
            dbase.close()
            return 'not turn'
    current_state = state_for_computer(sorted(occupied_ref))
    if len(current_state[0]) != 0:
        dbase.close()
        return 'winner'
    winning_moves = []
    for potential_X in unoccupied:
        imaginary_state = imagine_X(potential_X, occupied_ref)
        if len(imaginary_state[0]) > 0:
            winning_moves.append(tuple((1, potential_X)))
        else:
            for item in imaginary_state[1]:
                if item not in current_state[1]:
                    winning_moves.append(tuple((2, potential_X)))
    if len(sorted(winning_moves)) > 0:
        winners = [item for item in winning_moves if item[0] == 1]
        almost_winners = [item for item in winning_moves if item[0] == 2]
        if len(winners) > 0:
            move = random.choice(winners)
        else:
            move = random.choice(almost_winners)
        piece = 'X' + str(num_moves + 4)
        query = "UPDATE polls_cord SET XyCords= ? WHERE PieceId= ?"
        cur.execute(query, (potential_X, piece))
        num_moves += 1
        query = "UPDATE polls_cord SET XyCords= 'n' WHERE PieceId= 'pieceS'"
        cur.execute(query)
        dbase.commit()
    dbase.close()

def send_data(state, num_moves):
    dbase = sqlite3.connect('db.sqlite3')
    cur = dbase.cursor()
    for pair in state:
        cord = pair[0]
        piece = pair[1]
        if cord not in fixed:
            if piece != 0:
                query = "UPDATE polls_cord SET XyCords = ? WHERE PieceId = ?"
                cur.execute(query, (cord, piece))
            else:
                query = "SELECT * FROM polls_cord WHERE XyCords = ?"
                for row in cur.execute(query, [cord]):
                    if row[1] == 'player0':
                        query = "UPDATE polls_cord SET XyCords='none' WHERE PieceId = ?"
                        cur.execute(query, [row[2]])
    dbase.commit()
    dbase.close()
    comp_move(state, num_moves)

def decode_cords(state):
    new_state = []
    for i, t in enumerate(state):
        cord_num = t[0]
        cord = 'none'
        if cord_num == 0:
            cord = '12'
        if cord_num == 1:
            cord = '02'
        if cord_num == 2:
            cord = '22'
        if cord_num == 3:
            cord = '10'
        if cord_num == 4:
            cord = '11'
        if cord_num == 5:
            cord = '00'
        if cord_num == 6:
            cord = '01'
        if cord_num == 7:
            cord = '20'
        if cord_num == 8:
            cord = '21'
        new_state.append(tuple((cord, t[1][0])))
    return new_state

print ("Script running")
print ("Press Ctrl+C to stop")

try:
    num_moves = 0
    while (True):
        board_state_temp = []
        for i in range(9):
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            GPIO.setup(11, GPIO.OUT)
            GPIO.setup(12, GPIO.OUT)
            GPIO.setup(15, GPIO.OUT)
            GPIO.setup(16, GPIO.OUT)
            GPIO.output(11, S0_cycle[i])
            GPIO.output(12, S1_cycle[i])
            GPIO.output(15, S2_cycle[i])
            GPIO.output(16, S3_cycle[i])
            reader = MFRC522.MFRC522()
            (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
            (status, uid) = reader.MFRC522_Anticoll()
            if len(uid) == 5:
                if uid[0] == 51 or uid[0] == 83 or uid[0] == 99 or uid[0] == 227 or uid[0] == 243:
                    reader.MFRC522_SelectTag(uid)
                    board_state_temp.append(tuple((i, uid)))
                else:
                    board_state_temp.append(tuple((i, none)))
            else:
                board_state_temp.append(tuple((i, none)))
            reader.Close_MFRC522()
        board_state_temp.sort(key=lambda tup: tup[0])
        board_state.sort(key=lambda tup: tup[0])
        if board_state != board_state_temp:
            for index, t in enumerate(board_state_temp):
                if board_state[index] != board_state_temp[index]:
                    GPIO.setmode(GPIO.BOARD)
                    GPIO.setwarnings(False)
                    GPIO.setup(11, GPIO.OUT)
                    GPIO.setup(12, GPIO.OUT)
                    GPIO.setup(15, GPIO.OUT)
                    GPIO.setup(16, GPIO.OUT)
                    GPIO.output(11, S0_cycle[index])
                    GPIO.output(12, S1_cycle[index])
                    GPIO.output(15, S2_cycle[index])
                    GPIO.output(16, S3_cycle[index])
                    reader = MFRC522.MFRC522()
                    (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
                    (status, uid) = reader.MFRC522_Anticoll()
                    if len(uid) != 5:
                        uid = none
                    temp_find = tuple((index, uid))
                    if board_state_temp[index] != temp_find:
                        board_state_temp[index] = board_state[index]
            board_state = board_state_temp
            result = decode_cords(board_state)
            send_data(result, num_moves)
except KeyboardInterrupt:
    print ('QUIT')
    GPIO.cleanup()