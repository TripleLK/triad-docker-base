# Triad Docker Base

A Django-based data processing and analysis platform for scientific equipment data, with integrated AI processing capabilities and comprehensive web scraping tools.

## Overview

This project provides a comprehensive solution for processing, analyzing, and managing scientific equipment data. It features a Django web application with specialized tools for data scraping, AI-powered processing, and categorized content management.

### Key Features

- **Django Web Framework**: Full-featured web application with admin interface
- **AI Processing**: Integrated AI capabilities for data analysis and processing
- **Equipment Data Scraping**: Specialized tools for scientific equipment data collection
- **Categorized Content Management**: Advanced tagging and categorization system
- **Search Functionality**: Comprehensive search capabilities across all data
- **HTML Analysis Tools**: Specialized utilities for HTML content processing
- **Automated Development Workflow**: Git automation and AI collaboration framework

## Project Structure

```
triad-docker-base/
├── apps/                    # Django Applications
│   ├── ai_processing/       # AI-powered data processing
│   ├── base_site/          # Core site functionality
│   ├── categorized_tags/   # Content categorization system
│   ├── scrapers/           # Web scraping applications
│   ├── search/             # Search functionality
│   └── reload_from_git/    # Git integration utilities
├── config/                 # Django Configuration
│   ├── settings/           # Environment-specific settings
│   ├── environments/       # Environment configuration files
│   ├── urls.py            # URL routing
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── scripts/                # Utility Scripts (Organized by Function)
│   ├── equipment_scrapers/ # Equipment data collection scripts
│   ├── data_import/       # Data import and migration tools
│   ├── analysis/          # Data analysis and processing scripts
│   ├── tools/             # General utility tools
│   └── git_cleanup_push.py # Git automation script
├── docs/                   # Documentation
│   ├── api/               # API documentation
│   ├── development/       # Development guides
│   ├── equipment_integration/ # Equipment integration docs
│   └── triad_project_architecture.org # System architecture
├── data/                   # Reference Data
│   ├── reference/         # Reference datasets
│   └── sample_payloads/   # Example data structures
├── analysis_outputs/       # Analysis Results
│   ├── current/           # Current analysis results
│   └── archived/          # Historical analysis results
├── archive/                # Development Artifacts
│   ├── temporary_files/   # Temporary development files
│   └── historical/        # Historical development artifacts
├── static/                 # Static Files (CSS, JS, Images)
├── media/                  # User-uploaded Files
├── templates/              # Django Templates
├── tests/                  # Test Files
├── logs/                   # Application Logs
│   └── archived/          # Archived log files
├── manage.py              # Django Management Script
├── requirements.txt       # Python Dependencies
├── create_admin.py        # Admin User Creation Script
├── db.sqlite3            # Database (Development)
├── db.sqlite3.example    # Example Database
├── README.md              # This file
└── .gitignore            # Git Ignore Rules
```

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd triad-docker-base
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Development environment is pre-configured
   # Settings located in: config/environments/
   ```

4. **Initialize database**
   ```bash
   python manage.py migrate --settings=config.settings.dev
   ```

5. **Create admin user**
   ```bash
   python create_admin.py
   ```

6. **Run development server**
   ```bash
   python manage.py runserver --settings=config.settings.dev
   ```

7. **Access the application**
   - Web Interface: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/

## Configuration

### Django Settings

The project uses environment-specific settings:

- **Development**: `config.settings.dev`
- **Production**: `config.settings.prod` 
- **Environment Config**: `config/environments/`

### Environment Variables

Configuration files are located in `config/environments/` and include:
- Database connections
- API keys and secrets
- Feature flags
- Debug settings

## Development

### Django Applications

#### AI Processing (`apps/ai_processing/`)
Handles AI-powered data processing and analysis tasks.

#### Base Site (`apps/base_site/`)
Core website functionality and shared utilities.

#### Categorized Tags (`apps/categorized_tags/`)
Advanced tagging and categorization system for content organization.

#### Scrapers (`apps/scrapers/`)
Web scraping tools for scientific equipment data collection.

#### Search (`apps/search/`)
Comprehensive search functionality across all data sources.

#### Reload from Git (`apps/reload_from_git/`)
Git integration utilities for development workflow.

### Scripts and Tools

#### Equipment Scrapers (`scripts/equipment_scrapers/`)
Specialized tools for collecting data from scientific equipment manufacturers and suppliers.

#### Data Import (`scripts/data_import/`)
Migration and data import utilities for various data sources.

#### Analysis Tools (`scripts/analysis/`)
Data analysis scripts and HTML content processing utilities.

#### Development Tools (`scripts/tools/`)
General development utilities and helper scripts.

#### Git Automation (`scripts/git_cleanup_push.py`)
Automated git workflow for AI collaboration and development sessions.

### Testing

Run the test suite:
```bash
python manage.py test --settings=config.settings.dev
```

Test files are organized in the `tests/` directory with Django's standard test discovery.

### Development Workflow

The project includes an AI collaboration framework:

1. **Git Automation**: Automated commit and push workflow
2. **Development Tracking**: Progress tracking in `.project_management/`
3. **Change Documentation**: Comprehensive change logging
4. **Structured Handoffs**: Clear documentation for development continuity

## Data Management

### Reference Data (`data/`)
- **Reference datasets**: Core data for application functionality
- **Sample payloads**: Example data structures for development and testing

### Analysis Outputs (`analysis_outputs/`)
- **Current results**: Active analysis outputs
- **Archived results**: Historical analysis for reference

### Database
- **Development**: SQLite database (`db.sqlite3`)
- **Example data**: Sample database (`db.sqlite3.example`)
- **Migrations**: Django migrations in each app's `migrations/` directory

## API Documentation

Comprehensive API documentation is available in:
- `docs/api/` - Technical API specifications
- `docs/equipment_integration/` - Equipment-specific integration guides

## Deployment

### Development Deployment
```bash
python manage.py runserver --settings=config.settings.dev
```

### Production Considerations
- Configure production settings in `config.settings.prod`
- Set up proper database (PostgreSQL recommended)
- Configure web server (nginx + gunicorn recommended)
- Set up static file serving
- Configure logging and monitoring

## Architecture

The project follows Django best practices with:
- **Modular app structure**: Each app handles specific functionality
- **Environment-specific configuration**: Separate settings for dev/prod
- **Organized script structure**: Scripts categorized by function
- **Comprehensive documentation**: Architecture documented in `docs/triad_project_architecture.org`

## Contributing

### Development Standards
- Follow Django coding conventions
- Update documentation for structural changes
- Use the AI collaboration framework for development tracking
- Test changes thoroughly before committing

### AI Collaboration Framework
This project includes an advanced AI collaboration system:
- **Conversation logging**: All AI interactions are logged
- **Change tracking**: Comprehensive change documentation
- **Structured handoffs**: Clear priorities and next steps
- **Rule-based development**: Consistent AI behavior via cursor rules

## Support

For technical issues:
1. Check the documentation in `docs/`
2. Review the architecture file: `docs/triad_project_architecture.org`
3. Check development logs in `logs/`
4. Review AI collaboration logs in `.project_management/conversation_logs/`

## License

[License information to be added]

## Changelog

Major project phases:
- **Phase A Complete**: Full project reorganization with functional categorization
- **Phase B Complete**: Bulk move to final root-level structure
- **WSGI Cleanup**: Removed duplicate empty wsgi.py, proper config/wsgi.py maintained

For detailed change history, see `.project_management/conversation_logs/` and cleanup reports. 