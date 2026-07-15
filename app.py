from pathlib import Path
from datetime import datetime

from flask import Flask, abort, render_template, request, redirect, url_for,flash

from user_db import newUser, getUserByEmail, getUserById, updateUser, getUserQuests, isSessionBookedByUser, cancelBooking
from quest_db import create_quest, editQuest, newQuestSession, getQuests, getQuestById, ROLE_CAPACITY, getSessionsByQuestId, newBooking, getBooking, updateBooking, deleteQuest, deleteSession, getSessionByUserId, getReservationsByQuestId, getReservationsBySessionId, getQuestBySessionId, isUserBookedSession, getSessionWithDuration, getAllSessionsWithDuration, getUserSessionsWithDuration
from rules import *

from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from User import User


from PIL import Image


app = Flask(__name__)
app.config["SECRET_KEY"] = "Key"
login_manager = LoginManager()
login_manager.init_app(app)

QUEST_TYPES = ["Combat", "Exploration", "Puzzle", "Stealth", "Magic", "Survival"]
QUEST_LOCATIONS = ["Corlu", "Suleymanpasa", "Degirmenalti"]
QUEST_DIFFICULTIES = ["Easy", "Medium", "Hard", "Expert"]
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
QUEST_IMAGE_DIRECTORY = Path(app.root_path) / "static" / "images" / "quest-img"
PROFILE_IMAGE_DIRECTORY = Path(app.root_path) / "static" / "images" / "profile-imgs"
DEFAULT_QUEST_IMAGE = "/static/images/fallback.webp"
DEFAULT_BOSS_IMAGE = "/static/images/fallback.webp"
DEFAULT_PROFILE_IMAGE = "images/fallback.webp"
PROFILE_IMAGE_SIZE = 400
QUEST_IMAGE_SIZES = {
    "quest": (800, 450),
    "boss": (400, 400),
}


def save_quest_image(quest_img, image_type):
    img_name = ""

    if quest_img:
        img = Image.open(quest_img)

        width, height = img.size

        target_width, target_height = QUEST_IMAGE_SIZES[image_type]
        width_ratio = target_width / width
        height_ratio = target_height / height
        resize_ratio = max(width_ratio, height_ratio)

        new_width = round(width * resize_ratio)
        new_height = round(height * resize_ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        left = new_width / 2 - target_width / 2
        top = new_height / 2 - target_height / 2
        right = new_width / 2 + target_width / 2
        bottom = new_height / 2 + target_height / 2

        img = img.crop((left, top, right, bottom))

        secs = int(datetime.now().timestamp())

        ext = quest_img.filename.split(".")[-1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError("Images must be PNG, JPG, JPEG, or WEBP files.")

        img_name = image_type + "-" + str(secs) + "." + ext
        QUEST_IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        img.save(QUEST_IMAGE_DIRECTORY / img_name)

    return "/static/images/quest-img/" + img_name if img_name else None


def save_profile_image(profile_img):
    ext = profile_img.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Images must be PNG, JPG, JPEG, or WEBP files.")

    img = Image.open(profile_img)
    width, height = img.size

    resize_ratio = max(PROFILE_IMAGE_SIZE / width, PROFILE_IMAGE_SIZE / height)
    new_width = round(width * resize_ratio)
    new_height = round(height * resize_ratio)
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    left = new_width / 2 - PROFILE_IMAGE_SIZE / 2
    top = new_height / 2 - PROFILE_IMAGE_SIZE / 2
    right = new_width / 2 + PROFILE_IMAGE_SIZE / 2
    bottom = new_height / 2 + PROFILE_IMAGE_SIZE / 2
    img = img.crop((left, top, right, bottom))

    if ext in {"jpg", "jpeg"} and img.mode != "RGB":
        img = img.convert("RGB")

    secs = int(datetime.now().timestamp())
    img_name = "profile-" + str(secs) + "." + ext
    PROFILE_IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    img.save(PROFILE_IMAGE_DIRECTORY / img_name)

    return "images/profile-imgs/" + img_name


def questCanBeEdited(quest_id):
    if not sessionHasNoParticipants(getReservationsByQuestId(quest_id)):
        return False

    sessions = getSessionsByQuestId(quest_id)

    for session in sessions:
        if not participationCanChange(session):
            return False

    return True


def questCanBeDeleted(quest_id):
    if getReservationsByQuestId(quest_id):
        return False

    sessions = getSessionsByQuestId(quest_id)

    for session in sessions:
        if not participationCanChange(session):
            return False

    return True


@app.route('/')
def home():
    quests = getQuests()
    quests_with_days = []
    current_time = timeToMinutes(simulatedCurrentDay, simulatedCurrentTime)
    day_names = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday"
    }

    for quest in quests:
        quest_data = dict(quest)
        sessions = getSessionsByQuestId(quest["id"])
        days = []
        fully_booked = len(sessions) > 0
        closest_session = None
        closest_time = None

        for session in sessions:
            days.append(str(session["date"]))

            session_time = timeToMinutes(session["date"], session["time"])
            if session_time >= current_time:
                if closest_time is None or session_time < closest_time:
                    closest_time = session_time
                    closest_session = session

            if session["warrior"] > 0 or session["mage"] > 0 or session["healer"] > 0:
                fully_booked = False

        quest_data["days"] = ",".join(days)
        quest_data["fully_booked"] = fully_booked

        if closest_session:
            quest_data["closest_day"] = day_names[closest_session["date"]]
            quest_data["closest_time"] = closest_session["time"]
            quest_data["closest_location"] = closest_session["location"]
            quest_data["sort_time"] = closest_time
        else:
            quest_data["closest_day"] = None
            quest_data["closest_time"] = None
            quest_data["closest_location"] = None
            quest_data["sort_time"] = 999999

        quests_with_days.append(quest_data)

    quests_with_days.sort(key=lambda quest: (quest["sort_time"], quest["id"]))

    print("Quests:", quests)
    return render_template('index.html', index_nav=True, quests=quests_with_days,
                           quest_types=QUEST_TYPES,
                           quest_difficulties=QUEST_DIFFICULTIES)

@app.route('/signup')    
def signup():
    return render_template('signup.html', index_nav=False)

@app.route('/login')
def login():
    return render_template('login.html', index_nav=False)


@app.route('/quest-detail/<int:quest_id>')
def quest_detail(quest_id):
    quest = getQuestById(quest_id)
    if quest is None:
        abort(404)
    sessions = getSessionsByQuestId(quest_id)

    session_days = {
        session["date"]
        for session in sessions
    }

    weekdays = [
        (1, "Mo"),
        (2, "Tu"),
        (3, "We"),
        (4, "Th"),
        (5, "Fr"),
        (6, "Sa"),
        (7, "Su")
    ]
    selected_day = request.args.get("day", type=int)
    if selected_day not in range(1, 8):
        if sessions:
            selected_day = sessions[0]["date"]
        else:
            selected_day = 1

    selected_sessions = [
        session for session in sessions
        if session["date"] == selected_day
    ]

    changeable_session_ids = []
    deletable_session_ids = []
    for session in sessions:
        if participationCanChange(session):
            changeable_session_ids.append(session["sessionId"])

            if not getReservationsBySessionId(session["sessionId"]):
                deletable_session_ids.append(session["sessionId"])

    return render_template('quest_detail.html', quest=quest,
        quest_id=quest_id,
        sessions=sessions,
        selected_sessions=selected_sessions,
        session_days=session_days,
        weekdays=weekdays,
        user=current_user,
        selected_day=selected_day,
        can_edit=questCanBeEdited(quest_id),
        can_delete=questCanBeDeleted(quest_id),
        changeable_session_ids=changeable_session_ids,
        deletable_session_ids=deletable_session_ids,
        index_nav=False,
        isSessionBookedByUser=isSessionBookedByUser)



@app.route('/authenticate', methods=['POST'])
def authenticate():
    form_user = request.form.to_dict()
    u_email = form_user['email']
    u_password = form_user['password']

    user = getUserByEmail(form_user['email'])
    if user is None:
        flash('Invalid email or password.', 'error')
        return render_template('/login.html', index_nav=False)

    if not check_password_hash(user[2], form_user['password']):
        flash('Invalid email or password.', 'error')
        return render_template('/login.html', index_nav=False)    


    if user and check_password_hash(user[2], form_user['password']):
        new = User(id=user[0], email=user[1], password=user[2], name=user[3], surname=user[4], type=user[5], image=user[6])
        login_user(new)
        return redirect(url_for('home'))    



@app.route('/signup-adventurer', methods=['POST'])
def signup_adventurer():
    if request.method == 'POST' and getUserByEmail(request.form['email']) is None:
        u_email = request.form['email']
        u_password =generate_password_hash(request.form['password'])
        u_name = request.form['name']
        u_surname = request.form['surname']
        u_type = 'adventurer'
        u_image = DEFAULT_PROFILE_IMAGE

        u_name_capitalized = u_name.capitalize()
        u_surname_capitalized = u_surname.capitalize()

        newUser(u_email, u_password, u_name_capitalized, u_surname_capitalized, u_type, u_image)

        user = getUserByEmail(u_email)
        new_user = User(id=user[0], email=user[1], password=user[2], name=user[3], surname=user[4], type=user[5], image=user[6])
        login_user(new_user)

        return redirect(url_for('home'))
    else:
        flash('Email already exists. Please use a different email.', 'error')    
        return render_template('/signup.html', index_nav=False)    


@app.route('/profile')
@login_required
def profile():
    user = getUserById(current_user.id) 
    current = User(id=user[0], email=user[1], password=user[2], name=user[3], surname=user[4], type=user[5], image=user[6])
    user_quests = getUserQuests(user[0])

    for booking in user_quests:
        booking["canChange"] = participationCanChange(booking["session"])

    return render_template('profile.html', user=current, user_quests=user_quests, index_nav=False)


@app.route('/profile/image', methods=['POST'])
@login_required
def update_profile_image():
    profile_img = request.files.get('profile_img')
    if not profile_img or not profile_img.filename:
        flash('Please select an image.', 'error')
        return redirect(url_for('profile'))

    try:
        image_path = save_profile_image(profile_img)
    except (ValueError, OSError) as error:
        flash(str(error), 'error')
        return redirect(url_for('profile'))

    user = getUserById(current_user.id)
    updateUser(user[0], user[1], user[3], user[4], image_path)
    flash('Profile image updated.', 'success')
    return redirect(url_for('profile'))


@app.route('/book-quest/<int:session_id>', methods=['POST'])
@login_required
def book_quest(session_id):
    if current_user.type != 'adventurer':
        abort(403)

    session = getQuestBySessionId(session_id)
    if not session:
        abort(404)

    questId = session["questId"]
    user_role = request.form.get('user_role')
    number_of_places = request.form.get('number_of_places', type=int)

    if not validNumberOfPlaces(number_of_places):
        flash('You can only book for 1 or 2 people.', 'error')
        return redirect(url_for('quest_detail', quest_id=questId, index_nav=False))

    if not roleHasSpace(session, user_role, number_of_places):
        flash('There is not enough space for this role.', 'error')
        return redirect(url_for('quest_detail', quest_id=questId, index_nav=False))

    if isUserBookedSession(session_id, current_user.id):
        flash('You have already booked this session. You cannot book another one.', 'error')
        return  redirect(url_for('quest_detail', quest_id=questId, index_nav=False))

    if not userCanBookMore(getSessionByUserId(current_user.id)):
        flash('You have reached the maximum number of bookings allowed. You cannot book another one.', 'error')
        return  redirect(url_for('quest_detail', quest_id=questId, index_nav=False))

    if not userHasTimeAvailable(getSessionWithDuration(session_id), getUserSessionsWithDuration(current_user.id)):
        flash('This quest overlaps one of your booked quests.', 'error')
        return redirect(url_for('quest_detail', quest_id=questId, index_nav=False))
 
    newBooking(session_id, current_user.id, user_role, number_of_places)
    return redirect(url_for('my_quests', index_nav=False))


@app.route('/modify-booking/<int:session_id>', methods=['POST'])
@login_required
def modify_booking(session_id):
    if current_user.type != 'adventurer':
        abort(403)

    session = getSessionWithDuration(session_id)
    booking = getBooking(session_id, current_user.id)

    if session is None or booking is None:
        abort(404)

    if not participationCanChange(session):
        flash('This booking cannot be changed because the session starts in 8 hours or less.', 'error')
        return redirect(url_for('profile'))

    new_role = request.form.get('user_role')
    new_number_of_places = request.form.get('number_of_places', type=int)

    if not validNumberOfPlaces(new_number_of_places):
        flash('You can only book for 1 or 2 people.', 'error')
        return redirect(url_for('profile'))

    if new_role not in ('warrior', 'mage', 'healer'):
        flash('Select a valid role.', 'error')
        return redirect(url_for('profile'))

    available_spaces = session[new_role]
    if booking['userRole'] == new_role:
        available_spaces += booking['numberOfPlaces']

    if available_spaces < new_number_of_places:
        flash('There is not enough space for this role.', 'error')
        return redirect(url_for('profile'))

    updateBooking(session_id, current_user.id, new_role, new_number_of_places)
    flash('Booking updated successfully.', 'success')
    return redirect(url_for('profile'))


@app.route('/my-quests')
@login_required
def my_quests():
    reservations = getSessionByUserId(current_user.id)
    quests = []

    for reservation in reservations:
        session = getQuestBySessionId(reservation["sessionId"])

        if session:
            quest = getQuestById(session["questId"])

            if quest:
                quest_data = dict(quest)
                quest_data["booking_day"] = session["date"]
                quest_data["booking_time"] = session["time"]
                quest_data["booking_location"] = session["location"]
                quest_data["booking_role"] = reservation["userRole"]
                quest_data["booking_places"] = reservation["numberOfPlaces"]
                quests.append(quest_data)

    return render_template('my_quests.html', index_nav=False, my_quests=quests, user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/add-quest', methods=['GET', 'POST'])
@login_required
def add_quest():
    if current_user.type != 'guild_master':
        abort(403)

    if request.method == 'POST':
        q_title = request.form['q_title']
        q_description = request.form['q_description']
        q_duration = request.form['q_duration']
        q_type = request.form['q_type']
        q_difficulty = request.form['q_difficulty']
        q_boss_description = request.form['q_boss_description']

        session_days = request.form.getlist('session_day')
        session_times = request.form.getlist('session_time')
        session_locations = request.form.getlist('session_location')

        if not session_days or not (len(session_days) == len(session_times) == len(session_locations)):
            flash('Add at least one complete quest session.', 'error')
            return redirect(url_for('add_quest'))

        session_dates = []
        used_days = []

        for i in range(len(session_days)):
            day = session_days[i]
            time = session_times[i]
            location = session_locations[i]

            if not day and not time and not location:
                continue

            if not day or not time or not location:
                flash('Complete all fields for each session you use.', 'error')
                return redirect(url_for('add_quest'))

            if day in used_days:
                flash('A quest can only have one session on each day.', 'error')
                return redirect(url_for('add_quest'))

            used_days.append(day)
            session_dates.append({
                'q_day': day,
                'q_time': time,
                'q_location': location
            })

        if not session_dates:
            flash('Add at least one complete quest session.', 'error')
            return redirect(url_for('add_quest'))

        existing_sessions = getAllSessionsWithDuration()

        for session in session_dates:
            new_session = {
                'date': session['q_day'],
                'time': session['q_time'],
                'location': session['q_location'],
                'duration': q_duration
            }

            if not locationIsAvailable(new_session, existing_sessions):
                flash('Another quest already uses this location at that time.', 'error')
                return redirect(url_for('add_quest'))

        q_image_file = request.files.get('q_image')
        if not q_image_file or not q_image_file.filename:
            flash('A promotional image is required.', 'error')
            return redirect(url_for('add_quest'))

        try:
            q_image = save_quest_image(q_image_file, 'quest')
            q_boss_image = save_quest_image(request.files.get('q_boss_image'), 'boss') or DEFAULT_BOSS_IMAGE
        except (ValueError, OSError) as error:
            flash(str(error), 'error')
            return redirect(url_for('add_quest'))

        create_quest(q_title, q_description, q_duration, q_type, q_image,
                     session_dates, q_difficulty, q_boss_image, q_boss_description)
        return redirect(url_for('home'))
    return render_template('add_quest.html', index_nav=False,
                           quest_types=QUEST_TYPES,
                           quest_locations=QUEST_LOCATIONS,
                           quest_difficulties=QUEST_DIFFICULTIES)

@app.route('/edit-quest/<int:quest_id>', methods=['GET', 'POST'])
@login_required
def edit_quest(quest_id):
    if current_user.type != 'guild_master':
        abort(403)

    quest = getQuestById(quest_id)
    sessions = getSessionsByQuestId(quest_id)

    if not quest:
        abort(404)

    if not questCanBeEdited(quest_id):
        flash('This quest cannot be edited because it has a booking or starts in less than 8 hours.', 'error')
        return redirect(url_for('quest_detail', quest_id=quest_id))

    if request.method == 'POST':
        session_ids = request.form.getlist('session_id')
        days = request.form.getlist('session_day')
        times = request.form.getlist('session_time')
        locations = request.form.getlist('session_location')

        if not (len(session_ids) == len(days) == len(times) == len(locations) == 3):
            flash('Complete every session field.', 'error')
            return redirect(url_for('edit_quest', quest_id=quest_id))

        edited_sessions = []
        used_days = []
        existing_ids = []

        for session in sessions:
            existing_ids.append(str(session['sessionId']))

        for i in range(3):
            if session_ids[i] and session_ids[i] not in existing_ids:
                abort(400)

            if not days[i] and not times[i] and not locations[i]:
                continue

            if not days[i] or not times[i] or not locations[i]:
                flash('Complete every field for the session you use.', 'error')
                return redirect(url_for('edit_quest', quest_id=quest_id))

            if days[i] in used_days:
                flash('A quest can only have one session on each day.', 'error')
                return redirect(url_for('edit_quest', quest_id=quest_id))

            used_days.append(days[i])
            edited_sessions.append({
                'sessionId': session_ids[i],
                'date': days[i],
                'time': times[i],
                'location': locations[i],
                'duration': quest['duration']
            })

        other_sessions = []

        for session in getAllSessionsWithDuration():
            if session['questId'] != quest_id:
                other_sessions.append(session)

        for session in edited_sessions:
            if not participationCanChange(session):
                flash('A session must be more than 8 hours away to be edited.', 'error')
                return redirect(url_for('edit_quest', quest_id=quest_id))

            if not locationIsAvailable(session, other_sessions):
                flash('Another quest already uses this location at that time.', 'error')
                return redirect(url_for('edit_quest', quest_id=quest_id))

        for session in edited_sessions:
            if session['sessionId']:
                editQuest(
                    session['sessionId'],
                    session['date'],
                    session['time'],
                    session['location']
                )
            else:
                newQuestSession(
                    quest_id,
                    session['date'],
                    session['time'],
                    session['location']
                )

        flash('Quest sessions updated.', 'success')
        return redirect(url_for('quest_detail', quest_id=quest_id))

    return render_template('edit_quest.html', quest=quest,
                           sessions=sessions,
                           quest_locations=QUEST_LOCATIONS,
                           index_nav=False)


@app.route('/delete-session/<int:session_id>', methods=['POST'])
@login_required
def delete_session(session_id):
    if current_user.type != 'guild_master':
        abort(403)

    session = getSessionWithDuration(session_id)
    if session is None:
        abort(404)

    quest_id = session['questId']

    if getReservationsBySessionId(session_id) or not participationCanChange(session):
        flash('This session cannot be deleted because it has a booking or starts in 8 hours or less.', 'error')
        return redirect(url_for('quest_detail', quest_id=quest_id))

    deleteSession(session_id)
    flash('Session deleted successfully.', 'success')
    return redirect(url_for('quest_detail', quest_id=quest_id))


@app.route('/delete-quest/<int:quest_id>', methods=['POST'])
@login_required
def delete_quest(quest_id):
    if current_user.type != 'guild_master':
        abort(403)

    if getQuestById(quest_id) is None:
        abort(404)

    if not questCanBeDeleted(quest_id):
        flash('This quest cannot be deleted because it has a booking or starts in 8 hours or less.', 'error')
        return redirect(url_for('quest_detail', quest_id=quest_id))

    deleteQuest(quest_id)
    flash('Quest deleted successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/cancel-booking/<int:session_id>', methods=['POST'])
@login_required
def cancel_booking(session_id):
    if current_user.type != 'adventurer':
        abort(403)

    session = getSessionWithDuration(session_id)
    booking = getBooking(session_id, current_user.id)

    if session is None or booking is None:
        abort(404)

    if not participationCanChange(session):
        flash('This booking cannot be canceled because the session starts in 8 hours or less.', 'error')
        return redirect(url_for('my_quests'))

    cancelBooking(session_id, current_user.id)
    flash('Booking canceled successfully.', 'success')
    return redirect(url_for('my_quests'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', index_nav=False), 404

@login_manager.user_loader
def load_user(user_id):
    db_user = getUserById(user_id)
    if db_user:
        user = User(id=db_user[0], email=db_user[1], password=db_user[2], name=db_user[3], surname=db_user[4], type=db_user[5], image=db_user[6])
        return user
        
    return None
