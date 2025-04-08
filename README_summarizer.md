# Medical History Summarizer

This tool provides functionality to summarize a patient's medical history using the Groq LLM API.

## Files

- `summarize_history.py`: Core functionality for summarizing medical history

## Requirements

- Python 3.6+
- Requests
- python-dotenv
- mysql-connector-python

## Setup

1. Make sure you have the required environment variables set in your `.env` file:
   ```
   GROQ_API_KEY=your_groq_api_key
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=medical_assistant
   ```

2. Install the required packages:
   ```
   pip install requests python-dotenv mysql-connector-python
   ```

## Usage

### Command Line Interface

You can use the command-line interface to summarize a patient's medical history:

```
python summarize_history.py
```

The tool will prompt you to enter the patient's phone number and then display the summary.

## Integration with Main Application

To integrate this functionality with the main WhatsApp medical assistant application, you can:

1. Import the `summarize_medical_history` function from `summarize_history.py`
2. Call the function with the patient's phone number
3. Display the summary to the user

Example:

```python
from summarize_history import summarize_medical_history

# Get the summary
result = summarize_medical_history(phone_number)

if result["success"]:
    # Display the summary to the user
    print(result["summary"])
else:
    # Handle the error
    print(f"Error: {result['error']}")
``` 