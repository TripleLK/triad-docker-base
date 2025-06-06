# AI Processing App

This Django app provides an admin interface for interacting with AWS Bedrock AI models. It allows administrators to input a URL, which will be processed by a Bedrock AI model to extract structured information.

## Features

- Form to submit URLs for processing
- Integration with AWS Bedrock AI
- Track processing requests and their status
- View structured responses from the AI model

## Setup

1. Add the required AWS environment variables to your environment:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key
   - `AWS_REGION`: The AWS region (defaults to us-east-1)
   - `AWS_BEDROCK_PROMPT_ARN`: The ARN of the prompt to use (defaults to the one specified in the code)

2. Run migrations to create the necessary database tables:
   ```
   python manage.py makemigrations ai_processing
   python manage.py migrate
   ```

3. Restart your Django server

## Usage

1. Access the AI Processing section in the Wagtail admin menu
2. Enter a URL to process
3. The URL will be sent to AWS Bedrock for processing
4. View the structured response

## Security Considerations

- AWS credentials are stored as environment variables, not in the code
- Rate limiting should be implemented to prevent excessive API calls
- User input is validated before processing
- Error handling is implemented to handle API failures 