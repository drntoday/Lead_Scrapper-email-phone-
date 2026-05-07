# Lead Generation Pipeline

A compliance-first lead generation and validation system built with Flask.

## Features

- **Multi-source Extraction**: Google Maps, Online Directories, Company Websites
- **Email Validation**: Syntax check, MX record lookup, SMTP handshake verification
- **Catch-All Detection**: Identifies domains that accept all emails
- **Confidence Scoring**: 0-100% score based on validation layers passed
- **Deduplication**: Automatic duplicate detection and prevention
- **Export**: CSV, Excel, and JSON export formats
- **Dashboard**: Real-time lead statistics and management

## Project Structure

```
leadgen-pipeline/
├── app.py                  # Flask application factory
├── config.py               # Configuration settings
├── models.py               # Database models
├── routes.py               # API routes and views
├── requirements.txt        # Python dependencies
├── extractors/             # Data extraction modules
│   ├── __init__.py
│   ├── google_maps.py
│   ├── directory.py
│   └── website.py
├── validators/             # Validation modules
│   └── email_validator.py
├── templates/              # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── extract.html
│   └── validate.html
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── dashboard.js
│       ├── extract.js
│       └── validate.js
├── exports/                # Generated export files
└── .github/
    └── workflows/
        └── main.yml        # CI/CD pipeline
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open http://localhost:5000

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard homepage |
| GET | `/extract` | Extraction interface |
| GET | `/validate` | Validation interface |
| GET | `/api/leads` | Get all leads (paginated) |
| GET | `/api/leads/count` | Get lead statistics |
| POST | `/api/extract` | Start new extraction |
| POST | `/api/validate/email` | Validate single email |
| POST | `/api/validate/all` | Validate all unverified leads |
| DELETE | `/api/leads/clear` | Delete all leads |
| GET | `/api/leads/export/<format>` | Export leads (csv/xlsx/json) |

## Validation Process

1. **Syntax Check** (30 points): Validates email format using regex
2. **MX Record Lookup** (30 points): Verifies domain has mail servers
3. **SMTP Verification** (35 points): Confirms mailbox exists without sending email
4. **Catch-All Detection**: Identifies domains accepting all addresses

## Compliance

- Checks robots.txt before extraction
- Rate-limited requests (3-7 second delays)
- Only extracts publicly available data
- No emails sent during validation