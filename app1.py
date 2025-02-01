import instaloader
import time
import smtplib
from email.message import EmailMessage
from flask import Flask, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# Hardcoded username and password for demonstration
correct_username = "admin"
correct_password1 = "admin123"

# Email notification function
def send_email_notification(subject, body, sender_email, app_password, recipient_email):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)

# Monitor Instagram posts
def monitor_instagram_posts(usernames, sender_email, app_password, recipient_email):
    L = instaloader.Instaloader()
    monitoring_results = []
    
    for username in usernames:
        try:
            profile = instaloader.Profile.from_username(L.context, username)
            monitoring_results.append(f"Monitoring {username} for new posts...")

            posts = profile.get_posts()
            try:
                latest_post = next(posts)
                last_post_id = latest_post.shortcode
                monitoring_results.append(f"Last post detected for {username}: https://www.instagram.com/p/{last_post_id}/")
            except StopIteration:
                monitoring_results.append(f"No posts found for {username}")
                continue

            while True:
                try:
                    posts = profile.get_posts()
                    new_latest_post = next(posts)
                    new_post_id = new_latest_post.shortcode

                    if new_post_id != last_post_id:
                        post_url = f"https://www.instagram.com/p/{new_post_id}/"
                        monitoring_results.append(f"New post detected for {username}! Post URL: {post_url}")
                        send_email_notification(
                            f"New Instagram Post Alert for {username}!",
                            f"Check the new post at {post_url}",
                            sender_email, app_password, recipient_email
                        )
                        last_post_id = new_post_id
                    else:
                        monitoring_results.append(f"No new posts for {username}.")
                    time.sleep(300)
                except StopIteration:
                    monitoring_results.append(f"Could not fetch posts for {username}.")
                    break
                except Exception as e:
                    monitoring_results.append(f"Error monitoring {username}: {e}")
                    time.sleep(60)
        except Exception as e:
            monitoring_results.append(f"Failed to load profile for {username}: {e}")

    return monitoring_results

# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password1 = request.form['password']

    if username == correct_username and password1 == correct_password1:
        return jsonify({"message": f"Welcome, {username}!"}), 200
    else:
        return jsonify({"error": "Invalid username or password!"}), 401

# Instagram monitoring route
@app.route('/monitor', methods=['POST'])
def monitor():
    # Get form data
    data = request.get_json()
    usernames = data.get("usernames", "").split(",")
    sender_email = data.get("sender_email", "")
    app_password = data.get("app_password", "")
    recipient_email = data.get("recipient_email", "")
    
    if not (usernames and sender_email and app_password and recipient_email):
        return jsonify({"error": "Please provide all required fields!"}), 400
    
    results = monitor_instagram_posts(usernames, sender_email, app_password, recipient_email)
    return jsonify({"results": results}), 200

# Root route to check if the server is running
@app.route('/')
def home():
    return "Flask app is running!"

if __name__ == '__main__':
    app.run(debug=True)
