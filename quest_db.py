import sqlite3

ROLE_CAPACITY = {
    "warrior": 4,
    "mage": 3,
    "healer": 2
}



def create_quest(q_title, q_description, q_duration, q_type, q_image,
                 session_dates, q_difficulty, boss_image=None, boss_description=None):
    conn = sqlite3.connect('guild.db')
    cursor = conn.cursor()

    Warrior_capacity = ROLE_CAPACITY["warrior"]
    Mage_capacity = ROLE_CAPACITY["mage"]
    Healer_capacity = ROLE_CAPACITY["healer"]

    query = '''INSERT INTO Quests
               (Title, "warrior-empty", "mage-empty", "healer-empty", description,
                duration, type, image, "boss-image", "boss-description", level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    cursor.execute(query, (q_title, Warrior_capacity, Mage_capacity, Healer_capacity,
                           q_description, q_duration, q_type, q_image, boss_image,
                           boss_description, q_difficulty))
    quest_id = cursor.lastrowid

    for session in session_dates:
        query_session = "INSERT INTO QuestSessions (questId, date, time, location, warrior, mage, healer) VALUES (?,?,?,?,?,?,?)"
        cursor.execute(query_session, (quest_id, session['q_day'], session['q_time'],
                                       session['q_location'], Warrior_capacity,
                                       Mage_capacity, Healer_capacity))

    conn.commit()
    conn.close()

def editQuest(session_id, date, time, location):
    conn = sqlite3.connect("guild.db", timeout=10)
    cursor = conn.cursor()
    query = """UPDATE QuestSessions
               SET date = ?, time = ?, location = ?
               WHERE sessionId = ?"""
    cursor.execute(query, (date, time, location, session_id))
    conn.commit()
    conn.close()

def newQuestSession(quest_id, date, time, location):
    conn = sqlite3.connect("guild.db", timeout=10)
    cursor = conn.cursor()
    query = """INSERT INTO QuestSessions
               (questId, date, time, location, warrior, mage, healer)
               VALUES (?, ?, ?, ?, ?, ?, ?)"""
    cursor.execute(query, (quest_id, date, time, location,
                           ROLE_CAPACITY["warrior"],
                           ROLE_CAPACITY["mage"],
                           ROLE_CAPACITY["healer"]))
    conn.commit()
    conn.close()


def getQuests():
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM Quests"
    cursor.execute(query)
    quests = cursor.fetchall()
    conn.close()
    return quests


def getQuestById(quest_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM Quests WHERE id=?"
    cursor.execute(query, (quest_id,))
    quest = cursor.fetchone()
    conn.close()
    return quest


def newBooking(session_id, user_id, user_role, number_of_places):
    conn = sqlite3.connect('guild.db', timeout=10)
    cursor = conn.cursor()
    query = """INSERT INTO QuestReservation
               (sessionId, userId, userRole, numberOfPlaces)
               VALUES (?, ?, ?, ?)"""
    cursor.execute(query, (session_id, user_id, user_role, number_of_places))

    if user_role == "warrior":
        update_query = "UPDATE QuestSessions SET warrior = warrior - ? WHERE sessionId = ?"
    elif user_role == "mage":
        update_query = "UPDATE QuestSessions SET mage = mage - ? WHERE sessionId = ?"
    else:
        update_query = "UPDATE QuestSessions SET healer = healer - ? WHERE sessionId = ?"

    cursor.execute(update_query, (number_of_places, session_id))
    conn.commit()
    conn.close()


def getBooking(session_id, user_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM QuestReservation WHERE sessionId = ? AND userId = ?"
    cursor.execute(query, (session_id, user_id))
    booking = cursor.fetchone()
    conn.close()
    return booking


def updateBooking(session_id, user_id, new_role, new_number_of_places):
    if new_role not in ("warrior", "mage", "healer"):
        return False

    conn = sqlite3.connect('guild.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT userRole, numberOfPlaces FROM QuestReservation WHERE sessionId = ? AND userId = ?",
        (session_id, user_id)
    )
    old_booking = cursor.fetchone()

    if old_booking is None:
        conn.close()
        return False

    old_role = old_booking[0]
    old_number_of_places = old_booking[1]

    cursor.execute(
        f"UPDATE QuestSessions SET {old_role} = {old_role} + ? WHERE sessionId = ?",
        (old_number_of_places, session_id)
    )
    cursor.execute(
        f"UPDATE QuestSessions SET {new_role} = {new_role} - ? WHERE sessionId = ?",
        (new_number_of_places, session_id)
    )
    cursor.execute(
        """UPDATE QuestReservation
           SET userRole = ?, numberOfPlaces = ?
           WHERE sessionId = ? AND userId = ?""",
        (new_role, new_number_of_places, session_id, user_id)
    )
    conn.commit()
    conn.close()
    return True


def deleteQuest(quest_id):
    conn = sqlite3.connect('guild.db', timeout=10)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM QuestSessions WHERE questId = ?", (quest_id,))
    cursor.execute("DELETE FROM Quests WHERE id = ?", (quest_id,))
    conn.commit()
    conn.close()


def deleteSession(session_id):
    conn = sqlite3.connect('guild.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM QuestSessions WHERE sessionId = ?", (session_id,))
    conn.commit()
    conn.close()


def getQuestSessions(session_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM QuestSessions WHERE session_id=?"
    cursor.execute(query, (session_id,))
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def getSessionsByQuestId(quest_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM QuestSessions WHERE questId=?"
    cursor.execute(query, (quest_id,))
    sessions = cursor.fetchall()
    conn.close()
    return sessions    

def getSessionByUserId(user_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM QuestReservation WHERE userId=?"
    cursor.execute(query, (user_id,))
    reservations = cursor.fetchall()
    conn.close()
    return reservations       

def getReservationsByQuestId(quest_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """SELECT QuestReservation.*
               FROM QuestReservation
               JOIN QuestSessions ON QuestReservation.sessionId = QuestSessions.sessionId
               WHERE QuestSessions.questId=?"""
    cursor.execute(query, (quest_id,))
    reservations = cursor.fetchall()
    conn.close()
    return reservations


def getReservationsBySessionId(session_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM QuestReservation WHERE sessionId = ?"
    cursor.execute(query, (session_id,))
    reservations = cursor.fetchall()
    conn.close()
    return reservations

def getSessionWithDuration(session_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """SELECT QuestSessions.*, Quests.duration
               FROM QuestSessions
               JOIN Quests ON QuestSessions.questId = Quests.id
               WHERE QuestSessions.sessionId=?"""
    cursor.execute(query, (session_id,))
    session = cursor.fetchone()
    conn.close()
    return session

def getAllSessionsWithDuration():
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """SELECT QuestSessions.*, Quests.duration
               FROM QuestSessions
               JOIN Quests ON QuestSessions.questId = Quests.id"""
    cursor.execute(query)
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def getUserSessionsWithDuration(user_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """SELECT QuestSessions.*, Quests.duration
               FROM QuestReservation
               JOIN QuestSessions ON QuestReservation.sessionId = QuestSessions.sessionId
               JOIN Quests ON QuestSessions.questId = Quests.id
               WHERE QuestReservation.userId=?"""
    cursor.execute(query, (user_id,))
    sessions = cursor.fetchall()
    conn.close()
    return sessions

def getQuestBySessionId(session_id):
    conn = sqlite3.connect('guild.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM QuestSessions WHERE sessionId=?"
    cursor.execute(query, (session_id,))
    quest = cursor.fetchone()
    conn.close()
    return quest

def isUserBookedSession(session_id, user_id):
    sessions = getSessionByUserId(user_id)
    for session in sessions:
        if session["sessionId"] == session_id:
            return True
    return False
