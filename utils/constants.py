from enum import Enum

# Regex
UUID_PATTERN = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
DATE_PATTERN = '\\d{4}-\\d{2}-\\d{2}'

# User data keys
COOKIE = 'cookie'
TOKEN = 'token'
EMAIL = 'email'
PASSWORD = 'password'
LAST_MESSAGE = 'last_message'
STATE = 'state'
TO_STRIKETHROUGH = 'to_strikethrough'
TO_HIDE_KEYBOARD = 'to_hide_keyboard'

PROFILES = 'profiles'
SHORTCUTS = 'shortcuts'

TEMP = 'temp'
TRANSACTION = 'transaction'
VOLATILE = 'volatile'
STATIONS_DATA = 'stations_data'
TRACKING_LIST = 'tracking_list'

# Transaction keys
FROM_STATE_NAME, FROM_STATION_ID, FROM_STATION_NAME = 'from_state_name', 'from_station_id', 'from_station_name'
TO_STATE_NAME, TO_STATION_ID, TO_STATION_NAME = 'to_state_name', 'to_station_id', 'to_station_name'
DATE = 'date'
DEPARTURE_TIME, ARRIVAL_TIME = 'departure_time', 'arrival_time'
PRICE = 'price'

# Volatile keys
SEARCH_DATA = 'search_data'
TRIPS_DATA = 'trips_data'
TRIP_DATA = 'trip_data'
LAYOUT_DATA = 'layout_data'
BOOKING_DATA = 'booking_data'
OVERALL_PRICES = 'overall_prices'
PARTIAL_CONTENT = 'partial_content'

# Tracking item keys
TRACKING_UUID = 'tracking_uuid'
RESERVED_SEAT = 'reserved_seat'
SEATS_LEFT_BY_PRICES = 'seats_left_by_prices'
LAST_REMINDED = 'last_reminded'

# Bottom keyboard
TRACK_NEW_TRAIN = 'Track New Train 🚈'
VIEW_TRACKING = '👀 View Tracking'

# Inline keyboard
ADD_NEW_PROFILE = '+ New Profile'
ADD_NEW_PROFILE_DATA = 'New Profile'
ADD_NEW_SHORTCUT = '+ New Shortcut'
ADD_NEW_SHORTCUT_DATA = 'New Shortcut'
BACK = '↩️ Back'
BACK_DATA = 'Back'
YES = 'Yes'
YES_DATA = 'Yes'
NO = 'No'
NO_DATA = 'No'

CHANGE_PASSWORD_LABEL = '🔑 Change Password'
CHANGE_PASSWORD_DATA = 'Change Password'
DELETE_PROFILE = '🗑️ Delete'
DELETE_PROFILE_DATA = 'Delete Profile'

DELETE_SHORTCUT = '🗑️ Delete'
DELETE_SHORTCUT_DATA = 'Delete Shortcut'

START_TRACKING = '✅ Start Tracking!'
RESERVE = '🎟 Reserve'
RESERVE_DATA = 'Reserve'
REFRESHED_TRACKING = '🔄 Refresh'
REFRESH_TRACKING_DATA = 'Refresh Tracking'
CANCEL_TRACKING = 'Cancel Tracking'
CANCEL_TRACKING_DATA = 'Cancel Tracking'
REFRESH_RESERVED = '🔄 Refresh'
REFRESH_RESERVED_DATA = 'Refresh Reserved'
CANCEL_RESERVATION = 'Cancel Reservation'
CANCEL_RESERVATION_DATA = 'Cancel Reservation'

# Stages
# (
#     START,
#     ADD_EMAIL, ADD_PASSWORD,
#     PROFILE, SELECTED_PROFILE, CHANGE_PASSWORD,
#     ADD_FROM_STATE, ADD_FROM_STATION,
#     ADD_TO_STATE, ADD_TO_STATION,
#     SHORTCUT, SELECTED_SHORTCUT,
#     SET_EMAIL, SET_PASSWORD,
#     SET_FROM_STATE, SET_FROM_STATION,
#     SET_TO_STATE, SET_TO_STATION,
#     SET_DATE,
#     SET_TRIP,
#     SET_TRACK,
#     VIEW_TRACK,
#     RESERVED,
#     CLEAR
# ) = range(24)
START = 'start'
ADD_EMAIL, ADD_PASSWORD = 'add_email', 'add_password'
PROFILE, SELECTED_PROFILE, CHANGE_PASSWORD = 'profile', 'selected_profile', 'change_password'
ADD_FROM_STATE, ADD_FROM_STATION = 'add_from_state', 'add_from_station'
ADD_TO_STATE, ADD_TO_STATION = 'add_to_state', 'add_to_station'
SHORTCUT, SELECTED_SHORTCUT = 'shortcut', 'selected_shortcut'
SET_EMAIL, SET_PASSWORD = 'set_email', 'set_password'
SET_FROM_STATE, SET_FROM_STATION = 'set_from_state', 'set_from_station'
SET_TO_STATE, SET_TO_STATION = 'set_to_state', 'set_to_station'
SET_DATE = 'set_date'
SET_TRIP = 'set_trip'
SET_TRACK = 'set_track'
VIEW_TRACK = 'view_track'
RESERVED = 'reserved'
CLEAR = 'clear'


class Title(Enum):
    CREATE_TRACKING = 'Creating new tracking...'
    # CREATE_TRACKING_FROM_STATE = '⬛⬛⬛⬛⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_FROM_STATION = '🟩⬛⬛⬛⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_TO_STATE = '🟩🟩⬛⬛⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_TO_STATION = '🟩🟩🟩⬛⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_DATE = '🟩🟩🟩🟩⬛⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_TIME = '🟩🟩🟩🟩🟩⬛\n' + str(CREATE_TRACKING)
    # CREATE_TRACKING_PRICE = '🟩🟩🟩🟩🟩🟩\n' + str(CREATE_TRACKING)
    CREATE_TRACKING_FROM_STATE = '🌑 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_FROM_STATION = '🌑 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_TO_STATE = '🌒 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_TO_STATION = '🌒 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_DATE = '🌓 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_TIME = '🌔 ' + str(CREATE_TRACKING)
    CREATE_TRACKING_PRICE = '🌕 ' + str(CREATE_TRACKING)
    ADDED_TRACKING = '✅ New tracking added!'
    REFRESHED_TRACKING = '🔄 Tracking refreshed!'
    RESERVED = '🎟 New reservation made!'
    CANCEL_RESERVATION = '❎ Reservation cancelled!'
    TRACKING_NUM = '🔍 Tracking '
    ADD_PROFILE = '👤 Adding new profile...'
    ADDED_PROFILE = '✅ New profile added!'
    MANAGE_PROFILE = '👤 Managing profile...'
    UPDATED_PROFILE = '✅ Profile updated!'
    DELETED_PROFILE = '❎ Profile deleted!'
    ADD_SHORTCUT = '🔀 Adding new shortcut...'
    ADDED_SHORTCUT = '✅ New shortcut added!'
    MANAGE_SHORTCUT = '👤 Managing shortcut...'
    DELETED_SHORTCUT = '❎ Shortcut deleted!'


RANDOM_REPLIES = [
    'Stop sending stupid stuff la.',
    'Whoa, what is this you just sent?',
    'Wow, following instructions not included in your manifesto ke?',
    'You press lift button 10 times like it\'ll move faster. Genius.',
    'Malaysia Boleh... ignore instructions apparently.',
    'Forgot your keys again? Wah, so consistent.',
    'You missed the point so hard, even SPR pun blur.',
    'Why bring umbrella? Just enjoy the rain show lah.',
    'I said do X. You gave me Y with a side of political drama.',
    'Oh, you clicked "Reply All"? <b>Bravo</b>.',
    'This reply macam Parlimen debate — a lot of noise, no direction.',
    'Mic not working because it\'s on mute, but okay.',
    'Your answer is like the ringgit — steadily dropping.',
    'You boiling water with the kettle not plugged in? Magical thinking.',
    'Follow rules? What is this, an MACC raid?',
    'Send message, no context. Expect reply. Wah, psychic meh?',
    'You handled this like a traffic jam in KL — going nowhere fast.',
    'Crossing road while texting — real-life Frogger ah?',
    'So wrong it should be investigated by PAC.',
    'You forgot to save your work again? Legend.',
    'You skipped the rules like skipping voting day.',
    'Left rice cooker on "Keep Warm" for 3 days. Dinner or science project?',
    'This answer got more twists than a cabinet reshuffle.',
    'Ask for directions then don\'t listen. Solid plan.',
    'Eh, you joining Bersatu or just bersatu with chaos?',
    'Drink 5 cups of kopi then wonder why cannot sleep. Sherlock.',
    'Instructions were clearer than the government\'s SOPs. You still missed.',
    'Spend 1 hour choosing outfit for mamak. Iconic priorities.',
    'You just did what every budget proposal fears — confusion.',
    'Keep switching WiFi hoping it\'ll fix your attitude — and connection.',
    'This isn\'t an answer, it\'s a unity government of errors.',
    'Left wallet at home again? Sponsored by Touch ‘n Go frustration.',
    'So much deviation, even EC would call a recount.',
    'Open fridge 5 times to see the same kosong shelves. Inspiring.',
    'I ask for structure, you give me Langkah Sheraton.',
    'Put empty milk carton back in fridge. For what? Sentimental value?',
    'This reply is more fragile than coalition support.',
    'Overcooked Maggi. Truly a rare talent.',
    'Instruction: do A. You: declare emergency.',
    'Use phone with 1% battery and no charger. You like to live dangerously.',
    'Your logic has more holes than the budget audit.',
    'Complain it\'s hot, wear black. Fashion over survival huh?',
    'This is the political frog of answers. Lompat sana sini.',
    'Your idea of meal prep is tapau and hope.',
    'You answered like a manifestor — sounds nice, means nothing.',
    'Talk on speakerphone in public — yes, we all wanted to hear that breakup.',
    'Even Najib pun would be like "apa benda ni bro?"',
    'Shower but forget towel. What now, interpretive dance?',
    'That reply got less integrity than certain 1MDB transactions.',
    'Say "on the way" but haven\'t even showered. Classic.',
    'Like a general election: promised something, deliver nothing.',
    'Microwave metal container. Chef Gordon would cry.',
    'You took "wrong answer" and made it a political campaign.',
    'Trying to fix tech problem by yelling at it. Effective?',
    'More unpredictable than Malaysia\'s political alliances.',
    'Brought reusable bag, left it in car. Environmental hero.',
    'Instruction said one thing. You did a political U-turn.',
    'Forget to bring IC, then shocked cannot masuk building.',
    'That\'s not a reply, that\'s a press conference with no substance.',
    'Ask question during movie, then complain you blur. Self-inflicted.',
    'You treat my prompt like how GLCs treat transparency.',
    'Locked yourself out? Again? Must be a hobby now.',
    'Your answer made less sense than US inflation reports.',
    'Print document... no paper. What\'s the plan B?',
    'This feels like watching AI debate with Elon on X.',
    'Click "Remind me later" on software update for 3 years. Strong commitment.',
    'Global warming? No — it\'s your hot take melting logic.',
    'Forgot to turn off iron. Nice, now your house might glow.',
    'If your answer was a country, it\'d be in permanent crisis mode.',
    'Set 5 alarms. Still oversleep. Talent.',
    'This reply has more drama than the UN General Assembly.',
    'Throw clothes in washing machine, forget to press start. Inspiring.',
    'You handled this like Facebook handles misinformation.',
    'Use hairdryer as heater. Revolutionary!',
    'Even AI is tired, and I don\'t even sleep.',
    'Ordered food. Then sleep. Efficiency at its finest.',
    'That answer\'s as stable as Twitter under Musk.',
    'Left house lights on. Are you funding TNB single-handedly?',
    'You brought more chaos than a tech IPO in 2023.',
    'Use password "123456". Hacker also lazy to try.',
    'This take is colder than Europe\'s energy crisis.',
    'Charge phone overnight till 1000%. Need power for what? Mars trip?',
    'You\'re like the US Congress — always almost doing the right thing, but never quite.',
    'Forget to check fuel, now stranded. Bravo, Formula 0 driver.',
    'Your accuracy level is like crypto right now — pure speculation.',
    'Ask Siri for directions then ignore it. Got beef with AI ah?',
    'Instruction? You ghosted it harder than Meta ghosted the metaverse.',
    'Wore white shirt, eat curry. Culinary roulette.',
    'If confusion was a Superpower, you\'d be at UN Security Council.',
    'Missed bus while taking selfie. Sacrifice for content.',
    'This reply feels like it came from a deepfake version of reality.',
    'Put hot pot on plastic mat. Science experiment in progress.',
    'Your effort level rivals a cancelled climate summit.',
    'Try to toast bread in oven, burn whole thing. Artisan charcoal toast.',
    'You missed the target like COP meetings miss deadlines.',
    'Vacuum then spill Milo. The cycle of life.',
    'Like AI regulation — too little, too late.',
    'Dry clothes, it rains. Hang inside, sun comes out. Curse of laundry.',
    'So off-point, even ChatGPT wants to delete itself.',
    'Argue with Waze. Who\'s the real driver here?',
    'You delivered vibes, not results — very TikTok energy.',
    'Buy groceries. Forget the main thing you went for. As always.',
    'So much hot air, I thought this was a climate pledge.',
    'Didn\'t read manual, now the furniture looks like modern art.',
    'That answer = PR event with zero policy.',
    'Eat instant noodle with fork, drink soup with fork also? Innovation!',
    'You freestyled harder than AI-generated music tracks.',
    'Use shampoo as body wash. Two-in-one? Maybe not.',
    'You handled this like Netflix handles original scripts — not well.',
    'Forgot you put food on stove. Discover it hours later. Carbon delight.',
    'If I wanted a mess, I\'d just read Reddit drama.',
    'Use Google to check if you\'re sick. Now convinced you have 3 days left.',
    'Even fake news has more direction than this.',
    'Want to diet, eat salad... then drink teh tarik with extra susu.',
    'That\'s not an answer. That\'s a clickbait title with no content.',
    'Talk to plants, but not your friends. Bold priorities.',
    'Your reply is like a crypto pump — loud, then crash.',
    'Clean house, forget where you put everything. Genius organisation.',
    'You missed harder than NASA with a broken telescope.',
    'Buy gym membership, go once. Health investment complete.',
    'You\'re like Facebook\'s algorithm: chaotic and unasked for.',
    'Complain no money, still buy RM18 coffee. Inspirational finances.',
    'Even OpenAI would untrain itself after reading this.',
    'Keep pressing lift close button like it has feelings.',
    'That\'s not "outside the box," that\'s in another galaxy.',
    'Set alarm, put phone on silent. Truly next level.',
    'You\'re speedrunning the wrong-answer leaderboard.',
    'Throw clothes on "the chair" — every room has one.',
    'If instructions were taxes, you\'re clearly evading.',
    'Ask cat for life advice. Honestly, might be smarter.',
    'I said answer, not manifesto.',
    'Plan trip, forget passport. Beautiful chaos.',
    'Congratulations — you\'ve achieved "Opposition Reply" status.',
    'Type long message. Forget to send. Communication expert.',
    'You read the prompt, declared a state of emergency, and moved on.',
    'Send money to wrong account. Congratulations, you made someone\'s day.',
    'You turned a basic task into a political crisis.',
    'Update status every hour, still claim "low profile."',
    'Instruction? What instruction? #SabotageMode',
    'Buy plant, forget to water. Natural selection.',
    'You made AI question free will. Again.',
    'Start 5 tasks, complete none. Productivity... adjacent.',
    'So wrong, even Dewan Rakyat would adjourn over it.',
    'Watch cooking tutorial, end up burning kitchen. Close enough.',
    'Your reply has the stability of a fragile coalition.',
    'Vacuum carpet... after stepping on it with dirty feet. Progress?',
    'You answered like someone trying to explain 1MDB with crayons.',
    'Think of joke, laugh to self. People around just confused.',
    'You have the consistency of a cabinet line-up.',
    'Burn toast, make second toast... then burn again. Double down!',
    'This isn\'t a reply. It\'s a public relations disaster.',
    'Forgot food in car overnight. Surprise biology project.',
    'You\'re cosplaying as accuracy and failing.',
    'Tidy desk. Lose everything. Chaos is order now.',
    'This looks like it was written in the haze season — unclear and choking.',
    'Keep flashlight app on, battery dies. Classic move.',
    'You dropped the ball harder than a 5G rollout.',
    'Put cup on edge of table. Shocked when it falls.',
    'Instructions were clearer than SOPs during MCO. Still failed.',
    'You refill water bottle... with last night\'s coffee.',
    'You\'re giving serious "last-minute assignment" vibes.',
    'Complain about queue, still queue. Peak Malaysian behaviour.',
    'This is the manifesto of wrong answers.',
    'Scold mosquito, still get bitten. Justice not served.',
    'You answered like a budget debate — long, loud, pointless.',
    'Step on Lego. Blame floor. Logical.',
    'I said banana, you built a LRT station.',
    'Say "ok I sleep now," scroll phone for 2 more hours.',
    'So disconnected, even TMUnifi would be jealous.',
    'Need charger, use the slow one. Frustration simulator.',
    'This reply is like flood management — unprepared and messy.',
    'Forgot you had clothes in dryer. Now it\'s a wrinkle festival.',
    'You went rogue like a politician in party-hopping season.',
    'Switch TV input 100 times. Still no signal.',
    'You achieved the impossible: making less sense than social media.',
    'Message "where are you?" then walk away from phone.',
    'That reply needs a RCI — Royal Commission of Incompetence.',
    'Set up picnic, forgot the food. Just vibes.',
    'You\'re the political frog of logic. Hop, hop, wrong.',
    'Accidentally call someone, panic like FBI involved.',
    'Instructions: stabilise. You: destabilise and resign.',
    'Put cup upside down in sink. Now it\'s a mini pool.',
    'This reply should be censured by Parliament.',
    'Download 30 apps. Use 2. Storage well spent.',
    'Even PMX would say "this one no unity at all."',
    'Buy frozen stuff. Leave it in car. Soup, not supper.',
    'You read the prompt like politicians read manifestos — skim and ignore.',
    'Set reminder, forget to read it. The loop is complete.',
    'If replies were inflation, you just went hyper.',
    'Complain no time, watch 6 hours of random reels.',
    'That\'s not a solution, that\'s a parliamentary walkout.',
    'Use earphones, forget they\'re plugged in, walk away... goodbye phone.',
    'Instructions: solve. You: submit political theatre.',
    'Talk to self in supermarket. Staff probably monitoring already.',
    'Your accuracy just voted itself out.',
    'Leave soap on floor. Slippery adventure mode: unlocked.',
    'Even AG chambers can\'t justify this reply.'
    'Open can upside down. Beautiful mess.',
    'Try to catch falling phone, smack it harder. Athletic tragedy.',
    'Eat spicy food, drink Coke. Fireworks!',
    'Buy book to read, now it\'s a decorative piece.',
    'Say "quick shower," emerge 45 minutes later. Waterfall treatment.',
    'Put batteries in remote. Backwards. Again.',
    'Forget trash day. Now fridge has character.',
    'Trip on own foot. Talent or fate?',
    'Complain about no clothes, have full cupboard. A national mystery.'
]
