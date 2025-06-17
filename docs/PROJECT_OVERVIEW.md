# Triad Docker Base - Project Overview

## What This Project Does

**Triad Docker Base** is an AI-powered laboratory equipment content extraction and management system. The core mission is to automatically convert laboratory equipment web pages into structured database content through AI processing, with a focus on batch processing capabilities using AWS Bedrock.

### Primary Business Value
- **Automated Content Extraction**: Transform scattered lab equipment information from websites into structured, searchable database content
- **AI-Enhanced Processing**: Use advanced AI models to intelligently extract and categorize equipment specifications, models, and features
- **Batch Processing at Scale**: Process hundreds of equipment pages efficiently through AWS cloud infrastructure
- **Structured Data Output**: Generate clean, API-ready content for lab equipment catalogs and management systems

## Technology Stack

### Core Framework
- **Django 4.x** - Primary web framework
- **Python 3.x** - Programming language
- **SQLite/PostgreSQL** - Database (SQLite for development, PostgreSQL for production)
- **Django REST Framework** - API endpoints and serialization

### AI & Cloud Infrastructure
- **AWS Bedrock** - AI model hosting and batch inference processing
- **Amazon S3** - Cloud storage for batch processing inputs/outputs
- **AWS IAM** - Identity and access management for cloud resources
- **Multiple AI Models**: Anthropic Claude, Amazon Titan, Meta Llama (testing various providers)

### Content Processing
- **BeautifulSoup4** - HTML parsing and content extraction
- **XPath/CSS Selectors** - Precise content targeting on web pages
- **JSONL Format** - Batch processing data format for AI models
- **Wagtail CMS** - Content management for final equipment pages

### Development & Operations
- **Cursor IDE** - AI-assisted development environment
- **Git** - Version control with automated cleanup workflows
- **Django Management Commands** - Batch operations and administrative tasks
- **Org-mode** - Documentation and project tracking format

## Current Active Work (June 2025)

### CRITICAL PRIORITY: Batch Processing Model Combination Fix
**Status**: Thunder Ridge identified critical flaw, next model implementing fix
**Problem**: AWS Bedrock batch processing strips metadata from AI outputs, breaking model-to-equipment relationships
**Impact**: 15 equipment pages created successfully, but 0 equipment models (missing all model variations)

**What's Broken**:
```
Before Batch Processing (Working):
├── Equipment_overall_details.json     # Contains _processing_mode: "OVERALL_DETAILS"
├── Equipment_models_batch_1.json      # Contains _processing_mode: "MODEL_SUBSET" 
└── Equipment_models_batch_2.json      # Contains target_model_names: [...]

After Batch Processing (Broken):
├── record_1.json    # NO metadata, just AI output
├── record_2.json    # NO processing mode indicators
└── record_3.json    # NO file relationship information
```

**Solution Approaches**:
1. **Option A (Recommended)**: Modify AI prompts to include metadata in outputs
2. **Option B (Alternative)**: Smart file analysis to reconstruct relationships  
3. **Option C (Robust)**: Hybrid approach with fallback capabilities

### COMPLETED: AWS Bedrock Batch Inference System ✅
**Model**: Stellar Nexus completed full implementation
**Achievement**: Production-ready automated batch processing pipeline

**Capabilities**:
- ✅ Submit batch inference jobs to AWS Bedrock (any model)
- ✅ Real-time job monitoring and status tracking
- ✅ Automated results download and database integration
- ✅ Complete operational management with Django commands
- ✅ Error handling and dry-run testing capabilities

**Infrastructure Ready**:
- S3 bucket: `triad-bedrock-batch-processing`
- IAM role configured for Bedrock access
- 107 www.airscience.com records uploaded and ready for processing
- Production commands: `submit_batch_inference`, `monitor_batch_jobs`, `process_batch_results`

## What We're Doing With Batch Processing

### The Big Picture
We're building an automated pipeline that can:
1. **Crawl laboratory equipment websites** (completed)
2. **Extract structured content using AI selectors** (completed)
3. **Submit hundreds of pages to AWS Bedrock for AI processing** (completed)
4. **Convert AI outputs into searchable equipment database** (fixing now)

### Batch Processing Workflow
```mermaid
graph LR
    A[Website Pages] --> B[XPath Extraction]
    B --> C[JSONL Batch Files]
    C --> D[AWS Bedrock AI]
    D --> E[AI-Enhanced Content]
    E --> F[Database Import]
    F --> G[Lab Equipment Pages]
    G --> H[Equipment Models]
```

### Current Processing Volume
- **107 airscience.com equipment pages** ready for processing
- **Batch size**: 4-10 records per batch (configurable)
- **Processing time**: 15-30 minutes per batch job
- **Output**: Enhanced equipment descriptions, specifications, and model variations

### AI Processing Enhancement
**Input**: Raw HTML content + XPath-extracted fields
**AI Processing**: 
- Clean and structure equipment descriptions
- Extract technical specifications into organized groups
- Identify equipment model variations and their differences
- Generate SEO-friendly titles and summaries
- Categorize equipment by type and application

**Output**: Structured JSON ready for database import

## Project File Structure

### Django Applications
- `apps/content_extractor/` - **Main batch processing logic**
  - AWS Bedrock integration
  - Batch job management
  - XPath content extraction
  - S3 upload/download utilities

- `apps/base_site/` - **Core equipment models**
  - LabEquipmentPage model
  - EquipmentModel and specifications
  - Legacy API v1 endpoints

- `apps/lab_equipment_api/` - **Modern API v2**
  - REST framework endpoints
  - Batch operations support
  - Authentication and permissions

### Key Management Commands
```bash
# Batch Processing Pipeline
python manage.py batch_site_processor [domain] --max-pages 20
python manage.py submit_batch_inference --domain [domain] --input-s3-uri [uri]
python manage.py monitor_batch_jobs --watch
python manage.py process_batch_results --process-all-completed
python manage.py import_ai_json_to_equipment [directory]

# Content Extraction
python manage.py export_site_content [domain] --output-format jsonl
python manage.py test_selectors [domain] --url [specific-url]
```

### AWS Infrastructure
- **S3 Structure**: `bucket/batch-processing/[domain]/[timestamp]/`
- **Bedrock Models**: Testing Claude, Titan, Llama for best results
- **IAM Permissions**: Read/write S3, submit/monitor Bedrock jobs
- **Prompt Management**: Stored prompts for consistent AI processing

## Success Metrics

### Technical Success
- **Batch Processing Reliability**: >95% job completion rate
- **Data Quality**: AI-enhanced content with structured specifications
- **Model Relationship Integrity**: Equipment pages properly linked to model variations
- **Processing Speed**: Handle 100+ pages per hour through batch pipeline

### Business Success
- **Content Volume**: Process laboratory equipment catalogs at scale
- **Data Accuracy**: AI-improved descriptions and specifications
- **Search Capability**: Structured data enables advanced equipment search
- **Integration Ready**: Clean API endpoints for external system integration

## Next Model Priorities

### Immediate (This Week)
1. **Fix model combination bug** - Critical for equipment model relationships
2. **Test complete pipeline** - Verify 107 airscience.com records process correctly
3. **Validate database output** - Ensure LabEquipmentPage + EquipmentModel creation

### Medium Term (Next 2 Weeks)  
1. **Scale testing** - Process larger equipment catalogs
2. **Performance optimization** - Improve batch processing speed
3. **Quality assurance** - Enhance AI prompt quality and output validation

### Future Development
1. **Multi-domain processing** - Expand beyond airscience.com
2. **Real-time processing** - Single-page processing for immediate needs
3. **Advanced categorization** - ML-powered equipment classification

## Development Context

### AI Model Collaboration
- **Cursor Rules System**: Comprehensive workflow automation
- **Conversation Logging**: All decisions and changes tracked
- **Cleanup Protocols**: Structured handoffs between AI models
- **Active Work Tracking**: Clear priorities and status monitoring

### Quality Assurance
- **Test Data**: 104 batch processing outputs ready for validation
- **Verification Commands**: Django shell commands for database state checking
- **Error Handling**: Comprehensive logging and recovery procedures
- **Documentation**: Detailed technical documentation and decision rationale

This project represents a sophisticated AI-powered content processing pipeline with production-ready AWS infrastructure and Django-based data management. The current focus is completing the model relationship functionality to achieve full end-to-end automation. 