# Sahayak Backend

Django REST API backend for Sahayak Flutter application.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create superuser (for admin access):
```bash
python manage.py createsuperuser
```

5. Load initial service categories (optional):
```bash
python manage.py shell
>>> from services.models import ServiceCategory
>>> ServiceCategory.objects.create(name='AC', slug='ac', icon='ac')
>>> ServiceCategory.objects.create(name='Cleaning', slug='cleaning', icon='cleaning')
>>> ServiceCategory.objects.create(name='Plumber', slug='plumber', icon='plumber')
>>> ServiceCategory.objects.create(name='Electrician', slug='electrician', icon='electrician')
>>> ServiceCategory.objects.create(name='Carpenter', slug='carpenter', icon='carpenter')
>>> ServiceCategory.objects.create(name='Car-Wash', slug='car-wash', icon='car-wash')
>>> ServiceCategory.objects.create(name='Painter', slug='painter', icon='painter')
>>> ServiceCategory.objects.create(name='TV Repair', slug='tv-repair', icon='tv-repair')
>>> ServiceCategory.objects.create(name='Security', slug='security', icon='security')
```

6. Run development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /api/auth/users/register/` - User registration
- `POST /api/auth/users/login/` - User login
- `GET /api/auth/users/me/` - Get current user (requires authentication)

### Services
- `GET /api/services/categories/` - List all service categories

### Providers
- `POST /api/providers/register/` - Complete provider registration (all steps)
- `POST /api/providers/onboarding_step1/` - Step 1: Location and referral code (requires auth)
- `POST /api/providers/onboarding_step2/` - Step 2: Service selection (requires auth)
- `POST /api/providers/onboarding_step3/` - Step 3: Personal info and documents (requires auth)
- `GET /api/providers/my_profile/` - Get provider profile (requires auth)
- `GET /api/providers/status/` - Check verification status (requires auth)

## Provider Onboarding Flow

### Screen 1: Location & Referral Code
- Collect latitude, longitude, location string, and optional referral code
- Endpoint: `POST /api/providers/onboarding_step1/`

### Screen 2: Service Selection
- Select services the provider offers
- Endpoint: `POST /api/providers/onboarding_step2/`

### Screen 3: Personal Information & Documents
- Collect name, contact, address, profile photo, PAN card, registration certificate
- Endpoint: `POST /api/providers/onboarding_step3/`

After completing all steps, the provider status is set to "pending" and they cannot login until admin verifies and approves them.

## Admin Interface

Access the admin panel at `http://localhost:8000/admin/` to:
- View and verify service providers
- Approve/reject providers
- Manage service categories
- View user accounts

## File Structure

```
backend/
├── accounts/          # User authentication and management
├── providers/        # Service provider models and onboarding
├── services/         # Service categories
├── suvidha_connect/  # Main project settings
├── manage.py
└── requirements.txt
```

