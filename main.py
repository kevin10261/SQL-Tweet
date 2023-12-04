import sqlite3
import getpass
import re


def connect_db():
    """
    Connect to an SQLite database.

    This function prompts the user for the database name and establishes a connection to the specified database.

    Returns:
        sqlite3.Connection: A connection object to the SQLite database.
"""
    db_name = input("Input database name: ")
    conn = sqlite3.connect(db_name)
    conn.commit()
    return conn


def login_screen(conn):
    """
    Display a login screen with options to login, sign up, or exit.

    Args:
        conn (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str: The user ID of the logged-in user or None if the user chooses to exit.
    """
    while True:
        print("1. Login")
        print("2. Sign Up")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            loggedin = login(conn)
            if loggedin is not None:
                return loggedin
        elif choice == "2":
            usr = signup(conn)
            if usr is not None:
                return usr
        elif choice == "3":
                exit()
        else:
            print("Invalid choice. Please try again.")


def login(conn):
    """
    Authenticate a user by checking their credentials in the database.

    Args:
        conn (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str: The user ID of the logged-in user or None if login fails.
    """
    cursor = conn.cursor()
    count = 0
    while True:
        # getting user id and password
        usr = input("Enter user ID: ")
        pwd = getpass.getpass("Enter password: ")

        # query to get user id and password matching the input user id
        cursor.execute("SELECT usr, pwd FROM users WHERE usr = ?", (usr,))
        result = cursor.fetchone()

        if result:
            stored_usr, stored_pwd = result
            # if the password is the same then they can log in
            if pwd == stored_pwd:
                print("Login successful!")
                tweets_of_followee = get_tweets_of_followee(conn, usr)  # getting the tweets of the users that they follow
                printing_tweets(conn,usr, tweets_of_followee) # printing the tweets
                
                return stored_usr
            # else the password is incorrect
            else:
                print("Incorrect password, try again.")
        # otherwise the user was not found
        else:
            print("User not found, try again.")

        count += 1
        if count == 3:
            print("Too many attempts, bringing you back to main screen.")
            return None


def signup(conn):
    """
    Create a new user account and add it to the database.

    Args:
        conn (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str: The user ID of the newly created user or None if the user chooses not to log in.
    """
    cursor = conn.cursor()
    name = input("Enter Name: ")
    pwd = getpass.getpass("Enter password: ")
    email = input("Enter Email: ")
    city = input("Enter City: ")
    timezone = input("Enter Timezone: ")
    # query to geth max user id
    cursor.execute(""" 
        SELECT MAX(u.usr)
        FROM users u
""",)
    # add 1 to max id to create a new unique user id
    usr = cursor.fetchone()[0] + 1

    cursor.execute("""INSERT INTO users (usr,pwd, name,email,city,timezone) VALUES (:usr,:pwd,:name, :email, :city,:timezone)"""
                   ,{"usr":usr, "pwd": pwd,"name":name,"email": email,"city": city,"timezone": timezone})
    conn.commit()

    # giving user option to log in after signing up
    login_or_exit = input("Log in [Y/N]: ")
    # TO DO ADD LOGIN OPTION
    if login_or_exit.lower() == "y":
        print("Your user id is: " + str(usr))
        return usr
    elif login_or_exit.lower() == "n":
        print("Your user id is: " + str(usr))
        return None


def get_tweets_of_followee(conn, usr_id):
    """
    Retrieve tweets from users that the specified user follows.

    Args:
        conn (sqlite3.Connection): A connection object to the SQLite database.
        usr_id (str): User ID for whom to retrieve tweets.

    Returns:
        list: A list of tweets from followees, including original tweets and retweets.
    """
    cursor = conn.cursor() 
    # query to get the tweets of users they follow with retweets
    cursor.execute(""" 
    
    SELECT * 
    FROM (
        SELECT t.tid, t.writer, t.tdate AS date, t.text, t.replyto
        FROM tweets t
        JOIN follows f ON t.writer = f.flwee
        WHERE f.flwer = ?
        
        UNION ALL
        
        SELECT r.tid, r.usr, r.rdate AS date, t.text, t.replyto
        FROM retweets r
        JOIN tweets t ON r.tid = t.tid
        JOIN follows f ON r.usr = f.flwee
        WHERE f.flwer = ?
        ) AS combined
    ORDER BY date DESC;

""", (usr_id, usr_id))
    results = cursor.fetchall()
    return results


def printing_tweets(conn, usr, followee_tweets):
    """
    Display 5 tweets from followees in the user's feed.

    Args:
        conn (sqlite3.Connection): A connection object to the SQLite database.
        usr (str): User ID of the currently logged-in user.
        followee_tweets (list): List of tweets from followees.

    Returns:
        None
    """
    i = 0
    amount_of_tweets = len(followee_tweets)
    # if the user doesn't follow anyone
    if amount_of_tweets == 0:
        print("Follow people to get results in your feed!")
        return

    tweet_functions(conn, usr, followee_tweets)
    
    
def display_tweet_statistics(conn, tweet_id):
    cursor = conn.cursor()
    # Fetch the number of retweets
    cursor.execute("SELECT COUNT(*) FROM retweets WHERE tid = ?", (tweet_id,))
    retweet_count = cursor.fetchone()[0]
    
    # Fetch the number of replies
    cursor.execute("SELECT COUNT(*) FROM tweets WHERE replyto = ?", (tweet_id,))
    reply_count = cursor.fetchone()[0]
    
    print(f"Tweet ID: {tweet_id}")
    print(f"Retweets: {retweet_count}, Replies: {reply_count}")


def tweet_functions(conn, usr, followee_tweets):
    cursor = conn.cursor()
    rows = followee_tweets
    total_rows = len(rows)
    # sets the amount of tweets we want to appear
    batch_size = 5 
    final_batch = []
    # start of tweets
    start_idx = 0
     # condition for input validation
    stop_print = False
    # print tweets as long as the first index of batch is less than total
    while start_idx < total_rows and not stop_print: 
        # find end of the range of indexes that include current batch
        end_idx = start_idx + batch_size 
        # get current batch of tweets as own array
        current_batch = rows[start_idx:end_idx] 

        for i, row in enumerate(current_batch, start=start_idx + 1):
            # displaying each tweet with row number
            print(f"{i}. [tweet id: {row[0]}] [text: {row[3]}]")

       
        print('')

        # condition for input validation and asking if user wants to view more tweets
        valid_vm = False
        while valid_vm == False:
            view_more = input("More tweets [Y/N]: ").strip().lower()
            if view_more == 'y':
                valid_vm = True
            elif view_more == 'n':
                valid_vm = True
                stop_print = True
                break
            else:
                print("Invalid Option.")
        start_idx = end_idx
        final_batch = current_batch

    # if we passed the available amount of tweets and assuming we didn't break out manually
    if start_idx >= total_rows and stop_print == False:
        print("No more tweets.")

    # create index of tweets that can be seleceted based on amount of tweets displayed
    twt_range = start_idx - batch_size + len(final_batch)
    # condition for input validiation and asking user for specific tweet
    if twt_range > 0:
        valid_row = False
        while valid_row == False:
            retrieve_row = input("Enter the row number for more options [or s to skip]: ").strip().lower()
            if retrieve_row.isdigit():
                retrieve_row = int(retrieve_row)
                # given digit (if it is a valid number) should be in the range of available tweets
                if 1 <= retrieve_row <= twt_range:
                    valid_row = True
                    # fetch and display specific tweet
                    specific_row = rows[retrieve_row - 1]
                    cur_tid = specific_row[0]

                    #queries for finding reply and retweet counts, as well as the tweet writers name
                    find_rep = '''
                    SELECT t.tid, count(r.tid)
                    FROM tweets t
                    LEFT JOIN tweets r ON t.tid = r.replyto
                    WHERE t.tid == ?
                    GROUP BY t.tid
                                    '''
                    
                    find_ret = '''
                    SELECT t.tid, count(r.usr)
                    FROM tweets t
                    LEFT JOIN retweets r ON t.tid = r.tid
                    WHERE t.tid == ?
                    GROUP BY t.tid
                                '''
                    
                    find_name = '''
                    SELECT u.name
                    FROM tweets t
                    LEFT JOIN users u ON t.writer = u.usr
                    WHERE t.tid == ?
                    GROUP BY t.tid
                                '''
                    cursor.execute(find_rep,(cur_tid,))
                    rep_cnt = cursor.fetchone()[1]
                    
                    cursor.execute(find_ret,(cur_tid,))
                    ret_cnt = cursor.fetchone()[1]

                    cursor.execute(find_name, (cur_tid,))
                    usr_name = cursor.fetchone()[0]

                    #printing tweet information
                    print(f'''\nInformation: \n[tweet id: {cur_tid}] [writer id: {specific_row[1]}] [writer name: {usr_name}] [tdate: {specific_row[2]}]\n[replying to: {specific_row[4]}] [reply count: {rep_cnt}] [retweet count: {ret_cnt}]''')

                    # printing additional options
                    print("\nOptions:")
                    print("1. Reply")
                    print("2. Retweet")

                    # input condition and asking user if they want to choose an option
                    valid_option = False
                    while valid_option == False:
                        choice = input("Enter choice [Or s to skip]: ").lower()
                        if choice == '1':
                            valid_option = True
                            tweet = input("Compose your tweet: ")
                            compose_tweet(conn, usr, tweet, cur_tid)
                        elif choice == '2':
                            valid_option = True
                            retweet(conn, usr, cur_tid)
                        elif choice == 's':
                            valid_option = True
                            pass
                        else:
                            print("Invalid Option")
                else:
                    print("Row out of bounds. Try Again.")
            elif retrieve_row == 's':
                valid_row = True
                pass
            else:
                print("Invalid Option")


def retweet(conn, usr, tweet_id):
    cursor = conn.cursor()
    
    # Check if the user has already retweeted this tweet to avoid duplicate retweets
    cursor.execute("SELECT COUNT(*) FROM retweets WHERE usr = ? AND tid = ?", (usr, tweet_id))
    if cursor.fetchone()[0] > 0:
        print("You have already retweeted this tweet.")
        return

    # Get the current time for the retweet timestamp
    from datetime import datetime
    current_time = datetime.now().strftime('%Y-%m-%d')
    
    # Insert the retweet into the retweets table
    cursor.execute("INSERT INTO retweets (usr, tid, rdate) VALUES (?, ?, ?)", (usr, tweet_id, current_time))
    conn.commit()
    print("The tweet has been retweeted.")


def search_tweets(conn, current_user):
    cursor = conn.cursor()
    usr = current_user

    # define the batch size of tweets 
    batch_size = 5

    # stop condition for printing tweets
    stop_search = False
    while True and not stop_search:
        keywords_input = input("Enter keywords separated by spaces to filter tweets [or leave it empty to display all]: ").strip()
        keywords = keywords_input.split()

        # seperate arrays for the keyword conditions, mention specific conditions, and keyword alues
        keyword_conditions = []
        mention_conditions = []
        keyword_values = []

        for keyword in keywords:
            # check if keyword starts with #
            if keyword.startswith('#'):
                # if it starts with #, remove # and search for it in mentions table
                mention_conditions.append("m.term = ?")
                keyword_values.append(f"{keyword[1:]}")
            else:
                # otherwise search for it in tweet text
                keyword_conditions.append("t.text LIKE ?")
                keyword_values.append(f"%{keyword}%")
        
        if keyword_conditions or mention_conditions:
            # combine keyword and mention conditions for use in query
            conditions = " OR ".join(keyword_conditions + mention_conditions)
            
            query_template = f'''
                SELECT DISTINCT t.tid, t.writer, t.text, t.tdate, t.replyto
                FROM tweets t
                LEFT JOIN mentions m ON t.tid = m.tid
                WHERE {conditions}
                ORDER BY tdate DESC
            '''
            cursor.execute(query_template, keyword_values)
        else:
            cursor.execute('''
                SELECT tid, writer, text, tdate, replyto
                FROM tweets
                ORDER BY tdate DESC
                        ''')

        
        rows = cursor.fetchall()
        total_rows = len(rows)
        
        start_idx = 0
        stop_print = False
        final_batch = []
        while start_idx < total_rows and not stop_print:
            end_idx = start_idx + batch_size
            current_batch = rows[start_idx:end_idx]

            for i, row in enumerate(current_batch, start=start_idx + 1):
                # Process and display each row as needed with a row number
                print(f"{i}. [tweet id: {row[0]}] [text: {row[2]}]")

            # Ask the user if they want to view more rows
            print('')

            valid_vm = False
            while valid_vm == False:
                view_more = input("More tweets [Y/N]: ").strip().lower()
                if view_more == 'y':
                    valid_vm = True
                elif view_more == 'n':
                    valid_vm = True
                    stop_print = True
                    break
                else:
                    print("Invalid Option.")
            start_idx = end_idx
            final_batch = current_batch
    
        if start_idx >= total_rows and stop_print == False:
            print("No more tweets.")


        # create index of tweets that can be seleceted based on amount of tweets displayed
        twt_range = start_idx - batch_size + len(final_batch)
        # much same as previous function with main difference being the way the options are displayed
        if twt_range > 0:
            valid_row = False
            while valid_row == False:
                retrieve_row = input("Enter the row number for more options [or s to skip]: ").strip().lower()
                if retrieve_row.isdigit():
                    retrieve_row = int(retrieve_row)
                    if 1 <= retrieve_row <= twt_range:
                        valid_row = True
                        specific_row = rows[retrieve_row - 1]
                        cur_tid = specific_row[0]

                        # here is where the difference start, as in login the tweet information is displayed as soon as you select a tweet
                        print("\nOptions:")
                        # given the option to show it instead
                        print("1. More tweet information")
                        print("2. Reply")
                        print("3. Retweet")
                        valid_option = False
                        while valid_option == False:
                            choice = input("Enter choice [Or s to skip]: ").lower()
                            if choice == '1':
                                valid_option = True
        
                                
                                find_rep = '''
                                SELECT t.tid, count(r.tid)
                                FROM tweets t
                                LEFT JOIN tweets r ON t.tid = r.replyto
                                WHERE t.tid == ?
                                GROUP BY t.tid
                                                '''
                                
                                find_ret = '''
                                SELECT t.tid, count(r.usr)
                                FROM tweets t
                                LEFT JOIN retweets r ON t.tid = r.tid
                                WHERE t.tid == ?
                                GROUP BY t.tid
                                            '''
                                
                                find_name = '''
                                SELECT u.name
                                FROM tweets t
                                LEFT JOIN users u ON t.writer = u.usr
                                WHERE t.tid == ?
                                GROUP BY t.tid
                                            '''
                                cursor.execute(find_rep,(cur_tid,))
                                rep_cnt = cursor.fetchone()[1]

                                cursor.execute(find_ret,(cur_tid,))
                                ret_cnt = cursor.fetchone()[1]

                                cursor.execute(find_name, (cur_tid,))
                                usr_name = cursor.fetchone()[0]
                                
                                print(f'''\nInformation: \n[tweet id: {cur_tid}] [writer id: {specific_row[1]}] [writer name: {usr_name}] [tdate: {specific_row[3]}]\n[replying to: {specific_row[4]}] [reply count: {rep_cnt}] [retweet count: {ret_cnt}]''')
                            elif choice == '2':
                                valid_option = True
                                tweet = input("Compose your tweet: ")
                                compose_tweet(conn, usr, tweet, cur_tid)
                            elif choice == '3':
                                valid_option = True
                                retweet(conn, usr, cur_tid)
                            elif choice == 's':
                                valid_option = True
                                pass
                            else:
                                print("Invalid Option")
                    else:
                        print("Row out of bounds. Try Again.")
                elif retrieve_row == 's':
                    valid_row = True
                    pass
                else:
                    print("Invalid Option")
        # input condition and asking if the user wants to search with a new keyword
        valid_nk = False
        while valid_nk == False:
            another_search = input("Search with another keyword (Y/N)? ").strip().lower()
            if another_search == 'y':
                valid_nk = True
            elif another_search == 'n':
                valid_nk = True
                stop_search = True
                break
            else:
                print("Invalid Option.")


def compose_tweet(conn, usr, text, replyto):
    cursor = conn.cursor()

    # finding the max tid of all tweet ids
    cursor.execute(""" 
        SELECT MAX(t.tid)
        FROM tweets t
""",)
    # set the tid of this new tweet as one above the max to ensure unique status
    tid = cursor.fetchone()[0] + 1

    # insert tweet given the function arguments
    cursor.execute("INSERT INTO tweets(tid, writer, tdate, text, replyto) VALUES (?, ?, DATE('now'), ?, ?)", (tid, usr, text, replyto))

    # function that finds all words within the text string that contains a hashtag (includes if hashtag is at beginning, or back to back, and ignores case sensitivity)
    hashtags = re.findall(r'#(\w+)|(?<=\B#)(\w+)', text, flags=re.IGNORECASE)
    # adds and combines the captured group into a list
    hashtags = [group for group in sum(hashtags, ()) if group]
    # change all terms into lower case
    hashtags = [hashtag.lower() for hashtag in hashtags]

    # for each of the terms, check first if the term is already in the hashtags table
    for term in hashtags:
        cursor.execute('''
        SELECT *
        FROM hashtags
        WHERE term LIKE ?;
                        ''', (term,))
        value = cursor.fetchone()

        # if it is not, insert as a new term
        if value is None:
            cursor.execute("INSERT INTO hashtags (term) VALUES (?)", (term,))
        # always add the terms to the mentions table for every hashtag associated with that tweet
        cursor.execute('INSERT INTO mentions (tid, term) VALUES (?, ?)', (tid, term))
    conn.commit()
    if replyto is None:
        print("Your tweet has been posted.")    
    else:
        print("Your reply has been posted.")


def list_followers(conn, current_user):
    """
    List and display followers of the current user and allow the user to view details of a selected follower.

    Args:
        conn: The SQLite database connection.
        current_user (int): The user ID of the current user.

    This function retrieves and displays a list of followers of the current user, along with their usernames. 
    It allows the current user to select a follower to view more details or return to the previous menu.
    """

    cursor = conn.cursor()
    
    # Fetching all followers of the current user
    cursor.execute("SELECT flwer, name FROM follows JOIN users ON follows.flwer = users.usr WHERE flwee = ?", (current_user,))
    followers = cursor.fetchall()
    
    # If we have no followers, notify the user
    if not followers:
        print("You have no followers.")
        return
    
    # Display the list of followers
    print("\nYour Followers:")
    for idx, (follower_usr, follower_name) in enumerate(followers, 1):
        print(f"{idx}. {follower_name} (Username: {follower_usr})")
    
    # Ask the user to select a follower for more details
    try:
        choice = int(input("\nSelect a follower to see more details or 0 to go back: "))
        if choice == 0:
            return
        follower_usr, follower_name = followers[choice-1]
        display_follower_details(conn, follower_usr,current_user)
    except (ValueError, IndexError):
        print("Invalid choice.")


def display_follower_details(conn, follower_usr,current_usr):
    """
    Display details of a follower, including their information, tweet count, following count, and followers.
    Allows the current user to follow the displayed follower and view more of their tweets.

    Args:
        conn: The SQLite database connection.
        follower_usr (int): The user ID of the follower.
        current_usr (int): The user ID of the current user.

    This function fetches and displays various details about a follower, such as user's name, tweet count,
    following count, and followers. It also provides options for the current user to follow the displayed follower
    and view more of their tweets.
    """
    cursor = conn.cursor()
    

    # Fetching the number of tweets, users being followed, and followers for the selected user
    cursor.execute("SELECT name FROM users WHERE usr = ?", (follower_usr,))
    follower_name = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tweets WHERE writer = ?", (follower_usr,))
    tweet_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE flwer = ?", (follower_usr,))
    following_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE flwee = ?", (follower_usr,))
    follower_count = cursor.fetchone()[0]
    
    # Displaying the details
    print(f"\nDetails for {follower_name}:")
    print(f"Number of tweets: {tweet_count}")
    print(f"Following: {following_count} users")
    print(f"Followers: {follower_count}")
    
    # Fetching the 3 most recent tweets
    cursor.execute("SELECT text FROM tweets WHERE writer = ? ORDER BY tdate DESC LIMIT 3", (follower_usr,))
    recent_tweets = cursor.fetchall()
    if recent_tweets:
        print("\n3 Most Recent Tweets:")
        for tweet in recent_tweets:
            print("- " + tweet[0])
    
    # Asking the user for further actions
    action = input("\nChoose an action (follow/see more tweets/go back): ")
    if action == "follow":
        cursor.execute("SELECT 1 FROM follows WHERE flwer = ? AND flwee = ?", (current_usr, follower_usr))
        already_following = cursor.fetchone()
    
        if already_following:
            print(f"You are already following {follower_usr}.")
        else:
        # Implement the follow functionality
            cursor.execute("INSERT INTO follows(flwer, flwee, start_date) VALUES (?, ?, date('now'))", (current_usr,follower_usr))
            conn.commit()
            print(f"You are now following {follower_usr}!")
    elif action == "see more tweets":
        cursor.execute("""
                    SELECT text, tdate
                    FROM tweets
                    WHERE writer = ?
                    ORDER BY tdate DESC
                """, (follower_usr,))
        tweets = cursor.fetchall()
        for text, tdate in tweets:
            print(f"{tdate}: {text}")

    elif action == "go back":
        return
    else:
        print("Invalid action.")


def search_users(conn, current_user):
    """
    Search for users by a keyword (name or city) and display matching users. 
    Allows the current user to view details of a selected user from the search results.

    Args:
        conn: The SQLite database connection.
        current_user (int): The user ID of the current user.

    This function prompts the user to enter a keyword and searches for users whose names or cities contain 
    the keyword. It then displays the matching users and offers the option to view details of a selected user.
    """

    cursor = conn.cursor()

    keyword = input("Enter a keyword to search for users: ")

    # SQL query for searching users by name and city containing the keyword
    query = """
        SELECT usr, name, city
        FROM users
        WHERE name LIKE ? OR city LIKE ?
        ORDER BY
        CASE
            WHEN name LIKE ? THEN 0
            ELSE 1
        END,
        CASE
            WHEN name LIKE ? THEN LENGTH(name)
            ELSE LENGTH(city)
        END,
        usr
    """
    word = keyword
    keyword = f"%{keyword}%"

    # Execute the query with the keyword as a parameter for both name and city
    cursor.execute(query, (keyword, keyword, keyword, keyword))
    users = cursor.fetchall()

    if not users:
        
        print(f"No users found with the keyword '{word}'.")
        return

    displayed_users = 0
    show_more = 'y'  # Set an initial value
    while displayed_users < len(users) and show_more == 'y':
        print("\nMatching Users:")
        for i, (usr, name, city) in enumerate(users[displayed_users:displayed_users + 5], start=1):
            print(f"{i + displayed_users}. User ID: {usr}, Name: {name}, City: {city}")

        displayed_users += 5

        if displayed_users < len(users):
            valid_sm = False
            while not valid_sm:
                show_more = input("Show more users [Y/N]? ").strip().lower()
                if show_more == "y":
                    valid_sm = True
                elif show_more == 'n':
                    valid_sm = True
                    break  # Exit both loops when 'n' is entered
                else:
                    print("Invalid Response.")

    while True:
        try:
            choice = int(input("\nEnter the user number to see more details or 0 to go back: "))
            if choice == 0:
                return
            elif 1 <= choice <= len(users):
                selected_user = users[choice - 1]
                display_user_details(conn, selected_user, current_user)
            else:
                print("Invalid user number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def display_user_details(conn, user, current_user):
    """
    Display details of a user, including their information, tweet count, following count, and followers.
    Allows the current user to follow the displayed user and view more of their tweets.

    Arguments:
        conn: The SQLite database connection.
        user (tuple): A tuple containing user information (user ID, name, city).
        current_user (int): The user ID of the current user.

    This function fetches and displays various details about a user, such as user ID, name, city, tweet count,
    following count, and followers. It also provides options for the current user to follow the displayed user
    and view more of their tweets.
"""   
    cursor = conn.cursor()
    usr, name, city = user

    # Fetch the number of tweets, users being followed, and followers for the selected user
    cursor.execute("SELECT COUNT(*) FROM tweets WHERE writer = ?", (usr,))
    tweet_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE flwer = ?", (usr,))
    following_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follows WHERE flwee = ?", (usr,))
    follower_count = cursor.fetchone()[0]

    # Display the user details
    print(f"\nUser ID: {usr}")
    print(f"Name: {name}")
    print(f"City: {city}")
    print(f"Number of Tweets: {tweet_count}")
    print(f"Following: {following_count} users")
    print(f"Followers: {follower_count}")

    # Fetch up to 3 most recent tweets of the user
    cursor.execute("SELECT text, tdate FROM tweets WHERE writer = ? AND replyto IS NULL ORDER BY tdate DESC LIMIT 3", (usr,))
    recent_tweets = cursor.fetchall()

    if recent_tweets:
        print("\n3 Most Recent Tweets:")
        for i, (text, tdate) in enumerate(recent_tweets, start=1):
            print(f"{i}. {tdate}: {text}")

    while True:
        print("\nOptions:")
        print("1. Follow this user")
        print("2. See more tweets from this user")
        print("3. Go back")

        choice = input("Enter your choice: ")

        if choice == "1":
            follow_user(conn, current_user, usr)
        elif choice == "2":
            display_more_tweets(conn, usr)
        elif choice == "3":
            return
        else:
            print("Invalid choice. Please try again.")


def follow_user(conn, current_user, target_user):
    """
    Follow a target user and add the relationship to the database.

    Arguments:
        conn: The SQLite database connection.
        current_user (int): The user ID of the follower.
        target_user (int): The user ID of the user to be followed.

    This function checks if the current user is already following the target user. If not, it establishes
    a follow relationship between the current user and the target user, recording the start date.
"""
    cursor = conn.cursor()

    # Check if the current user is already following the target user
    cursor.execute("SELECT 1 FROM follows WHERE flwer = ? AND flwee = ?", (current_user, target_user))
    already_following = cursor.fetchone()

    if already_following:
        print(f"You are already following User ID {target_user}.")
    else:
        # Follow the target user
        cursor.execute("INSERT INTO follows(flwer, flwee, start_date) VALUES (?, ?, DATE('now'))", (current_user, target_user))
        conn.commit()
        print(f"You are now following User ID {target_user}!")


def display_more_tweets(conn, user_id, chunk_size=3):
    """
    Display tweets from a user in chunks, allowing the user to view more tweets if available.

    Arguments:
        conn: The SQLite database connection.
        user_id (int): The user's ID for whom to display tweets.
        chunk_size (int, optional): The number of tweets to display in each chunk. Default is 3.

    This function retrieves and displays tweets from the specified user, excluding replies, in chunks.
    It starts by showing the initial chunk of tweets and then continues to display more tweets based on user input.
"""
    cursor = conn.cursor()

    # Fetch all tweets of the user that are not replies, ordered by date.
    cursor.execute(
        "SELECT text, tdate FROM tweets WHERE writer = ? AND replyto IS NULL ORDER BY tdate DESC",
        (user_id,)
    )
    tweets = cursor.fetchall()

    if not tweets:
        print("No more tweets from this user.")
        return

    start_idx = 0  # Start index for the tweets to be displayed

    # Ask the user if they want to see the first chunk before entering the loop
    print(f"\nDisplaying {chunk_size} most recent tweets:")

    for i in range(chunk_size):
        if i < len(tweets):
            text, tdate = tweets[i]
            print(f"{i+1}. {tdate}: {text}")
        else:
            break  # Break the loop if there are fewer tweets than the chunk size

    start_idx += chunk_size  # Move the start index to skip the displayed tweets

    if len(tweets) <= 3:
        print("No more tweets")
        return
    
    while start_idx < len(tweets):
        end_idx = start_idx + chunk_size
        current_chunk = tweets[start_idx:end_idx]

        print("\nUser's Tweets:")
        for i, (text, tdate) in enumerate(current_chunk, start=start_idx + 1):
            print(f"{i}. {tdate}: {text}")

        if end_idx < len(tweets):
            show_more = input("\nShow more tweets (Y/N)? ").strip().lower()
            if show_more != "y":
                break

        start_idx += chunk_size  # Move the start index to skip the displayed tweets


def main():
    # Establish a connection to the database
    conn = connect_db()
    
    # Initialize the current_user to None
    current_user = None

    try:
        while True:
            # If no user is currently logged in, display the login screen
            if not current_user:
                current_user = login_screen(conn)

            # Display the main menu options
            print("\nMain Menu:")
            print("1. Search Tweets")
            print("2. Search Users")
            print("3. Compose Tweet")
            print("4. List followers")
            print("5. Logout")
            
            # Prompt the user for their choice
            choice = input("Enter choice: ")

            if choice == "1":
                # Option to search for tweets
                search_tweets(conn, current_user)
            elif choice == "2":
                # Option to search for users
                search_users(conn, current_user)
            elif choice == "3":
                # Option to compose and post a tweet
                text = input("Compose your tweet: ")
                compose_tweet(conn, current_user, text, None)
            elif choice == "4":
                # Option to list the followers of the current user
                print(current_user)
                list_followers(conn, current_user)
            elif choice == "5":
                # Option to log out, resetting the current_user to None
                current_user = None  # Logging out
                print("Logged out successfully!")
            else:
                # Handle invalid input
                print("Invalid choice. Try again.")

    finally:
        # Close the database connection when exiting the application
        if conn:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main()
