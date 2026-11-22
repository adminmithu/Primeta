import random
import re
import urllib.request
import json
from datetime import datetime, timedelta

# Rich realistic offline USA dataset
USA_MALE_FIRST = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Christopher",
    "Charles", "Daniel", "Matthew", "Anthony", "Donald", "Mark", "Paul", "Steven", "Andrew", "Kenneth",
    "Joshua", "Kevin", "Brian", "George", "Timothy", "Ronald", "Edward", "Jason", "Jeffrey", "Ryan",
    "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon",
    "Benjamin", "Samuel", "Gregory", "Alexander", "Frank", "Patrick", "Raymond", "Jack", "Dennis", "Jerry",
    "Tyler", "Aaron", "Jose", "Henry", "Adam", "Douglas", "Nathan", "Peter", "Zachary", "Kyle",
    "Walter", "Harold", "Jeremy", "Ethan", "Carl", "Keith", "Roger", "Gerald", "Christian", "Terry",
    "Sean", "Arthur", "Austin", "Noah", "Lawrence", "Jesse", "Joe", "Bryan", "Billy", "Jordan",
    "Albert", "Dylan", "Bruce", "Willie", "Gabriel", "Logan", "Alan", "Juan", "Wayne", "Roy",
    "Ralph", "Randy", "Eugene", "Vincent", "Russell", "Elijah", "Louis", "Bobby", "Philip", "Johnny"
]

USA_FEMALE_FIRST = [
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
    "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle",
    "Carol", "Amanda", "Dorothy", "Melissa", "Deborah", "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia",
    "Kathleen", "Amy", "Angela", "Shirley", "Anna", "Brenda", "Pamela", "Emma", "Nicole", "Helen",
    "Samantha", "Katherine", "Christine", "Debra", "Rachel", "Carolyn", "Janet", "Catherine", "Maria", "Heather",
    "Diane", "Ruth", "Julie", "Olivia", "Joyce", "Virginia", "Victoria", "Kelly", "Lauren", "Christina",
    "Joan", "Evelyn", "Judith", "Megan", "Andrea", "Cheryl", "Hannah", "Jacqueline", "Martha", "Gloria",
    "Teresa", "Ann", "Sara", "Madison", "Frances", "Kathryn", "Janice", "Jean", "Abigail", "Alice",
    "Julia", "Judy", "Sophia", "Grace", "Denise", "Amber", "Doris", "Marilyn", "Danielle", "Beverly",
    "Charlotte", "Marie", "Diana", "Brittany", "Theresa", "Kayla", "Alexis", "Tiffany", "Chloe", "Natalie"
]

USA_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
    "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper",
    "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez",
    "Powell", "Jenkins", "Perry", "Russell", "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes"
]

USA_LOCATIONS = [
    {"city": "New York", "state": "New York", "state_code": "NY", "zip": "10001", "area_code": "212"},
    {"city": "Los Angeles", "state": "California", "state_code": "CA", "zip": "90012", "area_code": "213"},
    {"city": "Chicago", "state": "Illinois", "state_code": "IL", "zip": "60601", "area_code": "312"},
    {"city": "Houston", "state": "Texas", "state_code": "TX", "zip": "77002", "area_code": "713"},
    {"city": "Phoenix", "state": "Arizona", "state_code": "AZ", "zip": "85001", "area_code": "602"},
    {"city": "Philadelphia", "state": "Pennsylvania", "state_code": "PA", "zip": "19102", "area_code": "215"},
    {"city": "San Antonio", "state": "Texas", "state_code": "TX", "zip": "78201", "area_code": "210"},
    {"city": "San Diego", "state": "California", "state_code": "CA", "zip": "92101", "area_code": "619"},
    {"city": "Dallas", "state": "Texas", "state_code": "TX", "zip": "75201", "area_code": "214"},
    {"city": "San Jose", "state": "California", "state_code": "CA", "zip": "95113", "area_code": "408"},
    {"city": "Austin", "state": "Texas", "state_code": "TX", "zip": "78701", "area_code": "512"},
    {"city": "Jacksonville", "state": "Florida", "state_code": "FL", "zip": "32099", "area_code": "904"},
    {"city": "San Francisco", "state": "California", "state_code": "CA", "zip": "94102", "area_code": "415"},
    {"city": "Columbus", "state": "Ohio", "state_code": "OH", "zip": "43215", "area_code": "614"},
    {"city": "Charlotte", "state": "North Carolina", "state_code": "NC", "zip": "28202", "area_code": "704"},
    {"city": "Indianapolis", "state": "Indiana", "state_code": "IN", "zip": "46204", "area_code": "317"},
    {"city": "Seattle", "state": "Washington", "state_code": "WA", "zip": "98101", "area_code": "206"},
    {"city": "Denver", "state": "Colorado", "state_code": "CO", "zip": "80202", "area_code": "303"},
    {"city": "Boston", "state": "Massachusetts", "state_code": "MA", "zip": "02108", "area_code": "617"},
    {"city": "Miami", "state": "Florida", "state_code": "FL", "zip": "33101", "area_code": "305"},
    {"city": "Atlanta", "state": "Georgia", "state_code": "GA", "zip": "30303", "area_code": "404"},
    {"city": "Las Vegas", "state": "Nevada", "state_code": "NV", "zip": "89101", "area_code": "702"}
]

STREET_NAMES = [
    "Oak Street", "Maple Avenue", "Washington Boulevard", "Main Street", "Cedar Lane",
    "Pine Road", "Elm Street", "Lakeview Drive", "Park Avenue", "Broadway",
    "Sunset Boulevard", "Highland Avenue", "Lincoln Street", "Chestnut Way", "River Road"
]

EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "hotmail.com"]


def generate_usa_identity_online():
    """Tries fetching fresh real US identity from RandomUser API with 2.5s timeout."""
    try:
        url = "https://randomuser.me/api/?nat=us"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=2.5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                user = data["results"][0]
                first = user["name"]["first"].capitalize()
                last = user["name"]["last"].capitalize()
                gender = user["gender"].capitalize()
                
                street = f"{user['location']['street']['number']} {user['location']['street']['name']}"
                city = user["location"]["city"].title()
                state = user["location"]["state"].title()
                postcode = str(user["location"]["postcode"])
                
                dob_raw = user["dob"]["date"][:10]
                age = user["dob"]["age"]
                
                email = user["email"]
                phone = user["phone"]
                username = user["login"]["username"]
                
                return {
                    "source": "online",
                    "first_name": first,
                    "last_name": last,
                    "full_name": f"{first} {last}",
                    "gender": gender,
                    "email": email,
                    "phone": phone,
                    "dob": dob_raw,
                    "age": age,
                    "address": street,
                    "city": city,
                    "state": state,
                    "zip_code": postcode,
                    "username": username
                }
    except Exception:
        pass
    
    # Fallback to local rich generator
    return generate_usa_identity_offline()


def generate_usa_identity_offline(gender_pref=None):
    """Instant offline realistic USA identity generation."""
    if not gender_pref:
        gender = random.choice(["Male", "Female"])
    else:
        gender = gender_pref.capitalize()
        
    if gender == "Male":
        first_name = random.choice(USA_MALE_FIRST)
    else:
        first_name = random.choice(USA_FEMALE_FIRST)
        
    last_name = random.choice(USA_LAST_NAMES)
    full_name = f"{first_name} {last_name}"
    
    loc = random.choice(USA_LOCATIONS)
    street_num = random.randint(100, 9999)
    street_name = random.choice(STREET_NAMES)
    address = f"{street_num} {street_name}"
    
    # Phone number with valid area code
    phone = f"+1 ({loc['area_code']}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
    
    # Age and DOB
    age = random.randint(21, 58)
    birth_year = datetime.now().year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    dob = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
    
    # Username and Email
    year_short = str(birth_year)[2:]
    rand_suffix = random.choice(["", str(random.randint(10, 99)), year_short])
    clean_first = re.sub(r'[^a-zA-Z]', '', first_name).lower()
    clean_last = re.sub(r'[^a-zA-Z]', '', last_name).lower()
    username = f"{clean_first}.{clean_last}{rand_suffix}"
    domain = random.choice(EMAIL_DOMAINS)
    email = f"{username}@{domain}"
    
    return {
        "source": "database",
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "gender": gender,
        "email": email,
        "phone": phone,
        "dob": dob,
        "age": age,
        "address": address,
        "city": loc["city"],
        "state": f"{loc['state']} ({loc['state_code']})",
        "zip_code": loc["zip"],
        "username": username
    }


def get_fake_name(gender=None):
    """Main wrapper that returns identity."""
    if gender:
        return generate_usa_identity_offline(gender)
    return generate_usa_identity_online()
