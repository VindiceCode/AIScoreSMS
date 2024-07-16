import azure.functions as func
import json
import pytest
from unittest.mock import patch, MagicMock
from categorize_sms import main

@pytest.fixture
def mock_env_variables():
    with patch.dict('os.environ', {
        'ANTHROPIC_API_KEY': 'test_anthropic_key',
        'OWNER_API_KEYS': '{"owner1": "test_hubspot_key_1", "owner2": "test_hubspot_key_2"}'
    }):
        yield

@pytest.mark.asyncio
async def test_main_success(mock_env_variables):
    # Mock the request
    req = func.HttpRequest(
        method='POST',
        body=json.dumps({
            'message': 'Test message',
            'contactId': '12345',
            'ownerId': 'owner1'
        }).encode('utf-8'),
        url='/api/categorize_sms'
    )

    # Mock the Anthropic API call
    with patch('categorize_sms.anthropic.Completion.create') as mock_anthropic:
        mock_anthropic.return_value.completion = 'New'

        # Mock the HubSpot API call
        with patch('categorize_sms.HubSpot') as mock_hubspot:
            mock_hubspot_instance = MagicMock()
            mock_hubspot.return_value = mock_hubspot_instance

            # Call the main function
            response = await main(req)

            # Assert the response
            assert response.status_code == 200
            body = json.loads(response.get_body())
            assert body['status'] == 'success'
            assert body['category'] == 'New'
            assert body['contactId'] == '12345'
            assert body['ownerId'] == 'owner1'

            # Assert that HubSpot was called with correct parameters
            mock_hubspot_instance.crm.contacts.basic_api.update.assert_called_once_with(
                contact_id='12345',
                properties={'sms_category': 'New'}
            )

@pytest.mark.asyncio
async def test_main_invalid_json(mock_env_variables):
    req = func.HttpRequest(
        method='POST',
        body=b'invalid json',
        url='/api/categorize_sms'
    )

    response = await main(req)

    assert response.status_code == 400
    body = json.loads(response.get_body())
    assert body['status'] == 'error'
    assert 'Invalid JSON' in body['error']

@pytest.mark.asyncio
async def test_main_missing_parameters(mock_env_variables):
    req = func.HttpRequest(
        method='POST',
        body=json.dumps({}).encode('utf-8'),
        url='/api/categorize_sms'
    )

    response = await main(req)

    assert response.status_code == 400
    body = json.loads(response.get_body())
    assert body['status'] == 'error'
    assert 'Please provide' in body['error']

@pytest.mark.asyncio
async def test_main_invalid_owner_id(mock_env_variables):
    req = func.HttpRequest(
        method='POST',
        body=json.dumps({
            'message': 'Test message',
            'contactId': '12345',
            'ownerId': 'invalid_owner'
        }).encode('utf-8'),
        url='/api/categorize_sms'
    )

    response = await main(req)

    assert response.status_code == 400
    body = json.loads(response.get_body())
    assert body['status'] == 'error'
    assert 'Invalid owner_id' in body['error']

@pytest.mark.asyncio
async def test_main_anthropic_api_error(mock_env_variables):
    req = func.HttpRequest(
        method='POST',
        body=json.dumps({
            'message': 'Test message',
            'contactId': '12345',
            'ownerId': 'owner1'
        }).encode('utf-8'),
        url='/api/categorize_sms'
    )

    with patch('categorize_sms.anthropic.Completion.create', side_effect=Exception('API Error')):
        response = await main(req)

        assert response.status_code == 500
        body = json.loads(response.get_body())
        assert body['status'] == 'error'
        assert 'An error occurred' in body['error']

@pytest.mark.asyncio
async def test_main_hubspot_api_error(mock_env_variables):
    req = func.HttpRequest(
        method='POST',
        body=json.dumps({
            'message': 'Test message',
            'contactId': '12345',
            'ownerId': 'owner1'
        }).encode('utf-8'),
        url='/api/categorize_sms'
    )

    with patch('categorize_sms.anthropic.Completion.create') as mock_anthropic:
        mock_anthropic.return_value.completion = 'New'

        with patch('categorize_sms.HubSpot') as mock_hubspot:
            mock_hubspot_instance = MagicMock()
            mock_hubspot_instance.crm.contacts.basic_api.update.side_effect = Exception('HubSpot API Error')
            mock_hubspot.return_value = mock_hubspot_instance

            response = await main(req)

            assert response.status_code == 500
            body = json.loads(response.get_body())
            assert body['status'] == 'error'
            assert 'An error occurred' in body['error']
