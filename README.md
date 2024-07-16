# SMS Categorization App

This Azure Function App categorizes SMS messages using the Anthropic API and updates HubSpot contacts with the categorization results.

flowchart LR
    subgraph Config ["Configuration"]
        direction TB
        Z1[/"User API Keys"\]:::config --> Z2{{"Key Validator"}}:::api
        Z3[/"Categories &<br>Prompts"\]:::config --> Z4{{"Config Manager"}}:::api
    end

    A([Incoming SMS]):::input --> B[/Azure Function\]:::process
    B --> Z2
    Z2 -->|Valid| C{Cached?}:::decision
    C -->|Yes| D[(Retrieve<br>Cached<br>Category)]:::data
    C -->|No| E{{Anthropic API}}:::api
    Z4 --> E
    E --> F[(Store<br>Category)]:::data
    D --> G[/Categorization<br>Complete\]:::process
    F --> G
    G -.-|Async Task| H{{Update<br>HubSpot}}:::api
    G --> I([HTTP Response]):::output

    subgraph Future ["Future Considerations"]
        direction TB
        Y1["ML Model<br>Integration"]:::future
        Y2["Real-time<br>Analytics"]:::future
        Y3["Multi-channel<br>Support"]:::future
    end

    classDef input fill:#FFA07A,stroke:#FF6347,stroke-width:2px,color:#000000,font-weight:bold;
    classDef output fill:#98FB98,stroke:#32CD32,stroke-width:2px,color:#000000,font-weight:bold;
    classDef process fill:#87CEFA,stroke:#4169E1,stroke-width:2px,color:#000000,font-weight:bold;
    classDef decision fill:#FFD700,stroke:#DAA520,stroke-width:2px,color:#000000,font-weight:bold;
    classDef data fill:#DDA0DD,stroke:#8B008B,stroke-width:2px,color:#000000,font-weight:bold;
    classDef api fill:#20B2AA,stroke:#008080,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef config fill:#F0E68C,stroke:#BDB76B,stroke-width:2px,color:#000000,font-weight:bold;
    classDef future fill:#B0C4DE,stroke:#4682B4,stroke-width:2px,color:#000000,font-weight:bold;

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

## Deployment to Azure

To deploy this function to Azure using the Azure CLI, follow these steps:

1. Install the Azure CLI if you haven't already:
   ```
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. Log in to your Azure account:
   ```
   az login
   ```

3. Set your subscription:
   ```
   az account set --subscription <your-subscription-id>
   ```

4. Create a resource group:
   ```
   az group create --name <resource-group-name> --location <location>
   ```

5. Create a storage account:
   ```
   az storage account create --name <storage-account-name> --location <location> --resource-group <resource-group-name> --sku Standard_LRS
   ```

6. Create a Function App:
   ```
   az functionapp create --resource-group <resource-group-name> --consumption-plan-location <location> --runtime python --runtime-version 3.9 --functions-version 4 --name <app-name> --os-type linux --storage-account <storage-account-name>
   ```

7. Set the necessary environment variables:
   ```
   az functionapp config appsettings set --name <app-name> --resource-group <resource-group-name> --settings ANTHROPIC_API_KEY=<your-anthropic-api-key>
   az functionapp config appsettings set --name <app-name> --resource-group <resource-group-name> --settings OWNER_API_KEYS='{"owner1": "hubspot_api_key_1", "owner2": "hubspot_api_key_2"}'
   ```

8. Deploy the function app:
   ```
   func azure functionapp publish <app-name>
   ```

Replace `<resource-group-name>`, `<location>`, `<storage-account-name>`, `<app-name>`, `<your-anthropic-api-key>`, and the HubSpot API keys with your actual values.

After deployment, your function will be accessible at:
`https://<app-name>.azurewebsites.net/api/categorize_sms`

Remember to secure your function using Azure AD authentication or function keys as appropriate for your use case.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.
