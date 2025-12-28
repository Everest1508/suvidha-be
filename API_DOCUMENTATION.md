# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

### Register User
```http
POST /api/auth/users/register/
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "password2": "securepassword123",
  "phone": "+1234567890",
  "role": "customer"  // or "provider"
}
```

### Login
```http
POST /api/auth/users/login/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepassword123"
}
```

### Get Current User
```http
GET /api/auth/users/me/
Authorization: Session <session_id>
```

## Service Categories

### List All Categories
```http
GET /api/services/categories/
```

Response:
```json
[
  {
    "id": 1,
    "name": "Cleaning",
    "slug": "cleaning",
    "icon": "cleaning",
    "description": "",
    "is_active": true
  }
]
```

## Provider Onboarding

### Complete Registration (All Steps at Once)
```http
POST /api/providers/register/
Content-Type: multipart/form-data

{
  "username": "provider123",
  "email": "provider@example.com",
  "password": "password123",
  "phone": "+1234567890",
  "latitude": "18.5204",
  "longitude": "73.8567",
  "location_string": "Pune, Maharashtra, India",
  "referral_code": "REF123",
  "service_ids": [1, 2, 3],
  "name": "John Doe",
  "contact": "+1234567890",
  "address": "123 Main Street, Pune",
  "profile_photo": <file>,
  "pan_card": <file>,
  "registration_certificate": <file>
}
```

### Step 1: Location & Referral Code
```http
POST /api/providers/onboarding_step1/
Authorization: Session <session_id>
Content-Type: application/json

{
  "latitude": "18.5204",
  "longitude": "73.8567",
  "location_string": "Pune, Maharashtra, India",
  "referral_code": "REF123"
}
```

### Step 2: Service Selection
```http
POST /api/providers/onboarding_step2/
Authorization: Session <session_id>
Content-Type: application/json

{
  "service_ids": [1, 2, 3]
}
```

### Step 3: Personal Information & Documents
```http
POST /api/providers/onboarding_step3/
Authorization: Session <session_id>
Content-Type: multipart/form-data

{
  "name": "John Doe",
  "contact": "+1234567890",
  "address": "123 Main Street, Pune",
  "profile_photo": <file>,
  "pan_card": <file>,
  "registration_certificate": <file>
}
```

### Get Provider Profile
```http
GET /api/providers/my_profile/
Authorization: Session <session_id>
```

### Check Verification Status
```http
GET /api/providers/status/
Authorization: Session <session_id>
```

Response:
```json
{
  "onboarding_step": 3,
  "is_onboarding_complete": true,
  "verification_status": "pending",
  "can_login": false,
  "verification_notes": null
}
```

## Verification Status

- `pending`: Provider has completed onboarding, waiting for admin approval
- `approved`: Provider is verified and can login
- `rejected`: Provider was rejected (cannot login)

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "error": "Your account is pending verification. Please wait for admin approval.",
  "verification_status": "pending",
  "onboarding_complete": true
}
```

### 404 Not Found
```json
{
  "error": "Provider profile not found"
}
```

