"""
Push notification utility functions for FCM HTTP v1 API.
"""
import requests
import json
import os
from django.conf import settings


def send_push_notification(fcm_token, title, body, data=None):
    """
    Send push notification using Firebase Cloud Messaging (FCM) HTTP v1 API.
    Requires FCM_SERVICE_ACCOUNT_JSON_PATH or FCM_PROJECT_ID to be set in Django settings.
    """
    if not fcm_token:
        print("⚠️ FCM token is empty. Skipping push notification.")
        return
    
    # Get project ID and service account JSON path from settings
    project_id = getattr(settings, 'FCM_PROJECT_ID', None)
    service_account_path = getattr(settings, 'FCM_SERVICE_ACCOUNT_JSON_PATH', None)
    
    if not project_id:
        print("⚠️ FCM_PROJECT_ID not configured. Skipping push notification.")
        print("   Set FCM_PROJECT_ID in settings.py (e.g., 'suvidha-2fb5d')")
        return
    
    if not service_account_path:
        print("⚠️ FCM_SERVICE_ACCOUNT_JSON_PATH not configured. Skipping push notification.")
        print("   Set FCM_SERVICE_ACCOUNT_JSON_PATH in settings.py")
        print("   Get the JSON file from: Firebase Console → Project Settings → Service Accounts → Generate new private key")
        return
    
    # Check if service account file exists
    if not os.path.exists(service_account_path):
        print(f"⚠️ Service account JSON file not found: {service_account_path}")
        print("   Please download the service account JSON file from Firebase Console")
        return
    
    try:
        # Import google-auth libraries
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/firebase.messaging']
        )
        
        # Get access token
        credentials.refresh(Request())
        access_token = credentials.token
        
        # FCM HTTP v1 API endpoint
        url = f'https://fcm.googleapis.com/v1/projects/{project_id}/messages:send'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        
        # HTTP v1 API payload structure
        payload = {
            'message': {
                'token': fcm_token,
                'notification': {
                    'title': title,
                    'body': body,
                },
                'data': {str(k): str(v) for k, v in (data or {}).items()},
                'android': {
                    'priority': 'high',
                    'notification': {
                        'sound': 'default',
                        'channel_id': 'default',
                    }
                },
                'apns': {
                    'headers': {
                        'apns-priority': '10',
                    },
                    'payload': {
                        'aps': {
                            'sound': 'default',
                        }
                    }
                }
            }
        }
        
        print(f"📤 Sending push notification via FCM HTTP v1 API")
        print(f"   Token: {fcm_token[:30]}...")
        print(f"   Title: {title}")
        print(f"   Body: {body}")
        print(f"   Project ID: {project_id}")
        print(f"   URL: {url}")
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Push notification sent successfully!")
            print(f"   Response: {result}")
        elif response.status_code == 401:
            print(f"❌ Authentication failed. Check service account JSON file.")
            print(f"   Response: {response.text[:200]}")
        elif response.status_code == 404:
            print(f"❌ Project not found. Check FCM_PROJECT_ID: {project_id}")
            print(f"   Response: {response.text[:200]}")
        else:
            print(f"❌ Failed to send push notification: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except ImportError as e:
        print(f"❌ Missing required package: {str(e)}")
        print("   Install: pip install google-auth google-auth-oauthlib google-auth-httplib2")
    except Exception as e:
        print(f"❌ Error sending push notification: {str(e)}")
        import traceback
        traceback.print_exc()

