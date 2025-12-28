# Test Login with cURL

## Test Login with Username

```bash
curl -X POST http://localhost:8000/api/auth/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

## Test Login with Email

```bash
curl -X POST http://localhost:8000/api/auth/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_email@example.com",
    "password": "your_password"
  }'
```

## Test Login with Email (Alternative field name)

```bash
curl -X POST http://localhost:8000/api/auth/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }'
```

## Example with Real Data

Replace `192.168.1.15:8000` with your server IP if different:

### Login with Username:
```bash
curl -X POST http://192.168.1.15:8000/api/auth/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ritesh_",
    "password": "your_password"
  }'
```

### Login with Email:
```bash
curl -X POST http://192.168.1.15:8000/api/auth/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "riteshmahale15@gmail.com",
    "password": "Ritesh@123"
  }'
```

## Expected Success Response

```json
{
  "user": {
    "id": 1,
    "username": "ritesh_",
    "email": "riteshmahale15@gmail.com",
    "phone": "1234567890",
    "role": "customer",
    "profile_photo": null,
    "date_joined": "2025-12-26T..."
  },
  "message": "Login successful"
}
```

## Expected Error Responses

### Invalid Credentials:
```json
{
  "error": "Invalid credentials"
}
```

### Missing Fields:
```json
{
  "error": "Username/Email and password are required"
}
```

### Provider Not Verified:
```json
{
  "error": "Your account is pending verification. Please wait for admin approval.",
  "verification_status": "pending",
  "onboarding_complete": true
}
```

## Save Session Cookie (for authenticated requests)

```bash
curl -X POST http://192.168.1.15:8000/api/auth/users/login/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "ritesh_",
    "password": "your_password"
  }'
```

Then use the cookie for subsequent requests:
```bash
curl -X GET http://192.168.1.15:8000/api/auth/users/me/ \
  -b cookies.txt
```



