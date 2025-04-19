import os
import psycopg2
import anthropic
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv(override=True)

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")
SUPABASE_POOLER_URI = os.getenv("SUPABASE_POOLER_URI")
CREDENTIALS_FILE = "../credentials.json"
TOKEN_FILE = "token.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_info(
            json.load(open(TOKEN_FILE)), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_all_labels():
    conn = psycopg2.connect(SUPABASE_POOLER_URI)
    cur = conn.cursor()
    cur.execute("SELECT name, description, color FROM email_labels")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    labels = []
    for row in rows:
        labels.append({"name": row[0], "description": row[1], "color": row[2]})
    return labels

def claude_multi_label(labels, email_text):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    categories = "\n".join([f"- {l['name']}: {l['description']}" for l in labels])
    prompt = (
        f"Given these categories:\n{categories}\n\n"
        "Which categories (by name) best fit the following email? "
        "Respond with a comma-separated list of label names, or 'none' if none fit.\n\n"
        f"Email:\n{email_text}"
    )
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    content = message.content[0].text.strip().lower()
    if content == 'none':
        return []
    return [l.strip() for l in content.split(",") if l.strip()]

def get_or_create_label(service, name, color):
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for label in labels:
        if label['name'] == name:
            return label['id']
    label_body = {
        "name": name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
        "color": {
            "backgroundColor": color or "#00FF00",
            "textColor": "#000000"
        }
    }
    new_label = service.users().labels().create(userId='me', body=label_body).execute()
    return new_label['id']

def tag_emails():
    labels = get_all_labels()
    label_map = {l['name']: l for l in labels}
    service = get_gmail_service()
    messages = service.users().messages().list(userId='me', maxResults=20).execute().get('messages', [])
    if not messages:
        return {"tagged": 0, "details": []}
    gmail_label_ids = {}
    existing_labels = service.users().labels().list(userId='me').execute().get('labels', [])
    for l in labels:
        found = next((g for g in existing_labels if g['name'] == l['name']), None)
        if found:
            gmail_label_ids[l['name']] = found['id']
    tagged_count = 0
    tagged_details = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_data.get('snippet', '')
        subject = next((h['value'] for h in msg_data['payload']['headers'] if h['name'].lower() == 'subject'), '')
        email_text = f"Subject: {subject}\nSnippet: {snippet}"
        matched_labels = claude_multi_label(labels, email_text)
        if not matched_labels:
            continue
        add_label_ids = []
        for label_name in matched_labels:
            if label_name not in gmail_label_ids:
                l = label_map.get(label_name)
                if not l:
                    continue
                label_id = get_or_create_label(service, l['name'], l['color'])
                gmail_label_ids[label_name] = label_id
            add_label_ids.append(gmail_label_ids[label_name])
        if add_label_ids:
            service.users().messages().modify(
                userId='me', id=msg['id'],
                body={"addLabelIds": add_label_ids}
            ).execute()
            tagged_count += 1
            tagged_details.append({"email_id": msg['id'], "labels": matched_labels})
    return {"tagged": tagged_count, "details": tagged_details}
