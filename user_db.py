import sqlite3

from quest_db import getQuestById




def newUser(u_email, u_password, u_name, u_surname, u_type, u_image=None):
    query = "INSERT INTO users (email, password, name, surname, type, image) VALUES (?, ?, ?, ?, ?, ?)" 

    conn = sqlite3.connect('guild.db')
    cursor = conn.cursor()

    cursor.execute(query, (u_email, u_password, u_name, u_surname, u_type, u_image))

    conn.commit()
    conn.close()


def getUserByEmail(u_email):
    query = "SELECT * FROM users WHERE email = ?"

    conn = sqlite3.connect('guild.db')
    cursor = conn.cursor()

    cursor.execute(query, (u_email,))
    user = cursor.fetchone()

    conn.close()
    return user

def getUserById(u_id):
    query = "SELECT * FROM users WHERE id = ?"

    conn = sqlite3.connect('guild.db')
    cursor = conn.cursor()

    cursor.execute(query, (u_id,))
    user = cursor.fetchone()

    conn.close()
    return user        

def updateUser(u_id, u_email, u_name, u_surname, u_image):
    if u_image:
        query = "UPDATE users SET email = ?, name = ?, surname = ?, image = ? WHERE id = ?"
        conn = sqlite3.connect('guild.db')
        cursor = conn.cursor()
        cursor.execute(query, (u_email, u_name, u_surname, u_image, u_id))
        conn.commit()
        conn.close()
    else:
        query = "UPDATE users SET email = ?, name = ?, surname = ? WHERE id = ?"
        conn = sqlite3.connect('guild.db')
        cursor = conn.cursor()
        cursor.execute(query, (u_email, u_name, u_surname, u_id))
        conn.commit()
        conn.close()


def getUserQuests(u_id):
    query = "SELECT * FROM QuestReservation WHERE userId = ?"

    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (u_id,))

    reservations = cursor.fetchall()

    quests = []
    for reservation in reservations:
        cursor.execute(
            "SELECT * FROM QuestSessions WHERE sessionId = ?",
            (reservation["sessionId"],)
        )
        session = cursor.fetchone()

        if session:
            cursor.execute(
                "SELECT * FROM Quests WHERE id = ?",
                (session["questId"],)
            )
            quest = cursor.fetchone()

            if quest:
                quests.append({
                    "quest": quest,
                    "session": session,
                    "userRole": reservation["userRole"],
                    "numberOfPlaces": reservation["numberOfPlaces"]
                })

    conn.close()
    return quests


def isSessionBookedByUser(session_id, user_id):
    query = "SELECT * FROM QuestReservation WHERE sessionId = ? AND userId = ?"

    conn = sqlite3.connect('guild.db')
    cursor = conn.cursor()

    cursor.execute(query, (session_id, user_id))
    reservation = cursor.fetchone()

    conn.close()
    if reservation:
        return True
    else:
        return False  

def cancelBooking(session_id, user_id):
    conn = sqlite3.connect('guild.db')
    cursor = conn.cursor()

    query = "SELECT userRole, numberOfPlaces FROM QuestReservation WHERE sessionId = ? AND userId = ?"
    cursor.execute(query, (session_id, user_id))
    result = cursor.fetchone()

    if result:
        user_role = result[0]
        numberOfPlaces = result[1]

       
        delete_query = "DELETE FROM QuestReservation WHERE sessionId = ? AND userId = ?"
        cursor.execute(delete_query, (session_id, user_id))

        if user_role == "warrior":
            update_query = "UPDATE QuestSessions SET warrior = warrior + ? WHERE sessionId = ?"
        elif user_role == "mage":
            update_query = "UPDATE QuestSessions SET mage = mage + ? WHERE sessionId = ?"
        elif user_role == "healer":
            update_query = "UPDATE QuestSessions SET healer = healer + ? WHERE sessionId = ?"
        
        cursor.execute(update_query, (numberOfPlaces, session_id))
        conn.commit()

    conn.close()        
