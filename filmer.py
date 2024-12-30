import os
import win32com.client
from datetime import datetime
import pytz

# Function to download attachments from emails
def download_attachments(subject, sender_email, start_date, end_date, email_folder='email'):
    # Ensure the folder exists
    if not os.path.exists(email_folder):
        os.makedirs(email_folder)

    # Initialize the Outlook application and get the inbox
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    inbox = namespace.GetDefaultFolder(6)  # 6 is the Inbox folder

    # Convert input date strings to datetime objects with timezone awareness
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Make the start and end dates timezone-aware (assumes local timezone)
    local_tz = pytz.timezone("America/New_York")  # Change to your local timezone if necessary
    start_date = local_tz.localize(start_date.replace(hour=0, minute=0, second=0))
    end_date = local_tz.localize(end_date.replace(hour=23, minute=59, second=59))

    # Format the dates as strings that can be used in the filter
    start_date_str = start_date.strftime("%m/%d/%Y %H:%M:%S")
    end_date_str = end_date.strftime("%m/%d/%Y %H:%M:%S")

    # Create the restriction filter string
    filter_string = f"[SenderEmailAddress] = '{sender_email}' AND [Subject] = '{subject}' AND [ReceivedTime] >= '{start_date_str}' AND [ReceivedTime] <= '{end_date_str}'"
    
    # Restrict the messages based on the filter
    filtered_messages = inbox.Items.Restrict(filter_string)

    # Sort messages by received time to ensure correct order
    filtered_messages.Sort("[ReceivedTime]", True)

    # Iterate through the filtered messages
    for msg in filtered_messages:
        try:
            # Check if the email has any attachments
            if msg.Attachments.Count > 0:
                for attachment in msg.Attachments:
                    attachment_name = attachment.FileName
                    attachment_path = os.path.join(email_folder, attachment_name)
                    print(f"Saving attachment: {attachment_name}")
                    attachment.SaveAsFile(attachment_path)
            else:
                print(f"No attachments for email: {msg.Subject} from {msg.SenderEmailAddress}")
        except Exception as e:
            # Catch any unexpected errors
            print(f"Error processing email '{msg.Subject}': {str(e)}")
            continue

# Main part of the script
if __name__ == "__main__":
    # Get user input for the sender email, date range, and subject
    sender_email = input("Enter the sender's email address: ")
    start_date = input("Enter the start date (YYYY-MM-DD): ")
    end_date = input("Enter the end date (YYYY-MM-DD): ")

    # Call the function to download attachments
    download_attachments(subject="Toto", sender_email=sender_email, start_date=start_date, end_date=end_date)
