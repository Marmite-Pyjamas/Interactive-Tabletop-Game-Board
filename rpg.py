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
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X1'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X2'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X3'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X4'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X5'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='X6'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='O1'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='O2'")
cur.execute("UPDATE polls_cord SET XyCords='00' WHERE PieceId='Enemy'")
cur.execute("UPDATE polls_cord SET XyCords='02' WHERE PieceId='W1'")
cur.execute("UPDATE polls_cord SET XyCords='10' WHERE PieceId='W2'")
cur.execute("UPDATE polls_cord SET XyCords='12' WHERE PieceId='W3'")
cur.execute("UPDATE polls_cord SET XyCords='20' WHERE PieceId='W4'")
cur.execute("UPDATE polls_cord SET XyCords='22' WHERE PieceId='W5'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='51'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='83'")
cur.execute("UPDATE polls_cord SET XyCords='none' WHERE PieceId='99'")
cur.execute("UPDATE polls_cord SET XyCords='n' WHERE PieceId='pieceS'")
dbase.commit()
dbase.close()

none = [0, 0, 0, 0 ,0]                                                              # EMPTY UID REF
spaces = ['00', '01', '02', '10', '11', '12', '20', '21', '22']                     # CORDS ON GRID
fixed = ['00', '02', '10', '12', '20', '22']                                        # FIXED CORDS FOR GAME
board_state = [tuple((0, none)),tuple((1, none)),tuple((2, none)),tuple((3, none)),
               tuple((4, none)),tuple((5, none)),tuple((6, none)),tuple((7, none)),
               tuple((8, none))]                                                    # EMPTY BOARD STATE

# ADDRESS CYCLE
S3_cycle = [0,0,0,0,0,0,1,1,1]
S2_cycle = [0,0,1,1,1,1,0,1,1]
S1_cycle = [0,0,0,0,1,1,0,0,1]
S0_cycle = [0,1,0,1,0,1,1,1,1]

# SEND PLAYER MOVE TO DATABASE
def send_data(state):
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

# TANSLATE GAME LOOP ITERATION TO SENSOR CORD
def decode_cords(state):
    new_state = []
    for i, t in enumerate(state):
        cord_num = t[0]
        cord = 'none'
        if cord_num == 0:
            cord = '01'
        if cord_num == 1:
            cord = '02'
        if cord_num == 2:
            cord = '21'
        if cord_num == 3:
            cord = '22'
        if cord_num == 4:
            cord = '11'
        if cord_num == 5:
            cord = '12'
        if cord_num == 6:
            cord = '00'
        if cord_num == 7:
            cord = '20'
        if cord_num == 8:
            cord = '10'
        new_state.append(tuple((cord, t[1][0])))
    return new_state

print ("Script running")
print ("Press Ctrl+C to stop")

try:
    num_moves = 0
    while (True):
        board_state_temp = []
        # CHECK EVERY SENSOR IN ADDRESS LOOP
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
        # IF BOARD STATE HAS CHANGED, DOUBLE CHECK THEN UPDATE DATABASE
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
            send_data(result)
except KeyboardInterrupt:
    print ('QUIT')
    GPIO.cleanup()
