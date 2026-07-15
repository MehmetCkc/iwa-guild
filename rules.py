simulatedCurrentDay = 1
simulatedCurrentTime = "08:00"


def timeToMinutes(day, time):
    hour, minute = time.split(":")
    return (int(day) - 1) * 1440 + int(hour) * 60 + int(minute)


def sessionsOverlap(firstSession, secondSession):
    firstStart = timeToMinutes(firstSession["date"], firstSession["time"])
    firstEnd = firstStart + int(firstSession["duration"])

    secondStart = timeToMinutes(secondSession["date"], secondSession["time"])
    secondEnd = secondStart + int(secondSession["duration"])

    return firstStart < secondEnd and secondStart < firstEnd


def locationIsAvailable(newSession, otherSessions):
    for session in otherSessions:
        sameLocation = session["location"] == newSession["location"]

        if sameLocation and sessionsOverlap(newSession, session):
            return False

    return True


def userHasTimeAvailable(newSession, bookedSessions):
    for session in bookedSessions:
        if sessionsOverlap(newSession, session):
            return False

    return True


def userCanBookMore(reservations):
    return len(reservations) < 3


def validNumberOfPlaces(numberOfPlaces):
    return numberOfPlaces == 1 or numberOfPlaces == 2


def roleHasSpace(session, role, numberOfPlaces):
    if role not in ("warrior", "mage", "healer"):
        return False

    return session[role] >= numberOfPlaces


def sessionHasNoParticipants(reservations):
    return len(reservations) == 0


def participationCanChange(session):
    currentTime = timeToMinutes(
        simulatedCurrentDay, simulatedCurrentTime
    )
    sessionTime = timeToMinutes(session["date"], session["time"])

    return sessionTime - currentTime > 8 * 60
