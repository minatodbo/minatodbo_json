import os
import win32com.client
from datetime import datetime

# Function to download attachments from emails
def download_attachments(subject, start_date, end_date, email_folder='email'):
    # Ensure the folder exists
    if not os.path.exists(email_folder):
        os.makedirs(email_folder)

    # Initialize the Outlook application and get the inbox
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    inbox = namespace.GetDefaultFolder(6)  # 6 is the Inbox folder
    messages = inbox.Items

    # Sort messages by received time to ensure correct date range filtering
    messages.Sort("[ReceivedTime]", True)

    # Convert input date strings to datetime objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    # Iterate through the messages
    for msg in messages:
        # Filter based on date range and subject
        if msg.Subject == subject and start_date <= msg.ReceivedTime <= end_date:
            print(f"Found email: {msg.Subject} from {msg.ReceivedTime}")
            
            # Check if the email has any attachments
            if msg.Attachments.Count > 0:
                for attachment in msg.Attachments:
                    attachment_name = attachment.FileName
                    attachment_path = os.path.join(email_folder, attachment_name)
                    print(f"Saving attachment: {attachment_name}")
                    attachment.SaveAsFile(attachment_path)

# Main part of the script
if __name__ == "__main__":
    # Get user input for date range
    start_date = input("Enter the start date (YYYY-MM-DD): ")
    end_date = input("Enter the end date (YYYY-MM-DD): ")

    # Call the function to download attachments
    download_attachments(subject="Toto", start_date=start_date, end_date=end_date)
