# SMS Categorization App

This Azure Function App categorizes SMS messages using the Anthropic API and updates HubSpot contacts with the categorization results.

## Prerequisites

- Python 3.9 or later
- Azure Functions Core Tools
- An Anthropic API key
- HubSpot API keys for each owner

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sms-categorization-app.git
   cd sms-categorization-app
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `local.settings.json` file in the project root with the following content:
   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "AzureWebJobsStorage": "",
       "ANTHROPIC_API_KEY": "your_anthropic_api_key_here",
       "OWNER_API_KEYS": "{\"owner1\": \"hubspot_api_key_1\", \"owner2\": \"hubspot_api_key_2\"}"
     }
   }
   ```
   Replace `your_anthropic_api_key_here` with your actual Anthropic API key, and add the appropriate HubSpot API keys for each owner.

## Running Locally

To run the function app locally:

1. Make sure you're in the project root directory and your virtual environment is activated.

2. Start the function app:
   ```
   func start
   ```

## Testing Locally

To test the function locally using bash:

1. Start the function app as described above.

2. In a new terminal window, use curl to send a POST request to the function:
   ```bash
   curl -X POST http://localhost:7071/api/categorize_sms \
   -H "Content-Type: application/json" \
   -d '{
     "message": "I'm interested in getting a mortgage quote",
     "contactId": "12345",
     "ownerId": "owner1"
   }'
   ```

   Replace the message, contactId, and ownerId with appropriate test values.

3. You should receive a JSON response with the categorization result.

## Running Tests

To run the unit tests:

1. Make sure you're in the project root directory and your virtual environment is activated.

2. Run the tests using pytest:
   ```
   pytest
   ```

## Deployment

To deploy this function to Azure, follow the Azure Functions deployment documentation, ensuring that you set up the necessary environment variables (ANTHROPIC_API_KEY and OWNER_API_KEYS) in your Azure Function App settings.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
