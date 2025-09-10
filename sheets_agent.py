import ssl
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from googleapiclient.discovery import Resource
from pydantic_ai.settings import ModelSettings
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior
from google_apis import create_service
from load_models import GEMINI_MODEL


@dataclass
class SheetsDependencies():
    sheets_service: Resource
    spreadsheet_id: str

class SheetsResult(BaseModel):
    request_status: bool = Field(description='Status pf the request')
    result_details: str = Field(description='Details of the request result')

def init_google_sheets_client() -> Resource:
    client_secret = 'credentials.json'
    API_NAME = 'sheets'
    API_VERSION = 'v4'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = create_service(client_secret, API_NAME, API_VERSION, SCOPES)
    return service
   

sheets_agent = Agent(
    model=GEMINI_MODEL,
    deps_type=SheetsDependencies,
    output_type=SheetsResult,
    system_prompt="""
    You are a Google Sheets agent to help me manage my Google Sheets tasks.

    When making API calls, wait 1 second between each request to avoid rate limits.
    """,
    model_settings=ModelSettings(timeout=10),
    retries=3
)

@sheets_agent.tool(retries=2)
def add_sheet(ctx: RunContext[SheetsDependencies], sheet_name: str) -> Any:
    """
    Adds a new sheet to an existing Google Spreadsheet

    Args:
        service: Google Sheets API service object
        spreadsheet_id: ID of the target spreadsheet
        sheet_name: Name for the new sheet

    Returns:
        Response from the API after adding the sheet
    """
    try:
        print(f'Calling add_sheet to add sheet "{sheet_name}"')
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]
        }
        response = ctx.deps.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=ctx.deps.spreadsheet_id,
            body=request_body
        ).execute()

        return response
    except (Exception, UnexpectedModelBehavior) as e:
        return f'An error occurred: {str(e)}'

    except ssl.SSL_ERROR_SSL as e:
        raise ModelRetry(f'An error occurred: {str(e)}. Please try again')

@sheets_agent.tool(retries=2)
def delete_sheet(ctx: RunContext[SheetsDependencies], sheet_name: str) -> Any:
    """
    Deletes a sheet from an existing Google Spreadsheet by sheet name

    Args:
        ctx: Run context containing sheets service and spreadsheet ID
        sheet_name: Name of the sheet to delete

    Returns:
        Response from the API after deletion
    """
    print(f'Calling delete_sheet to delete sheet "{sheet_name}')
    sheet_metadata = ctx.deps.sheets_service.spreadsheets().get(
        spreadsheetId=ctx.deps.spreadsheet_id
    ).execute()

    sheet_id = None
    for sheet in sheet_metadata.get('sheets', ''):
        if sheet['properties']['title'] == sheet_name:
            sheet_id = sheet['properties']['sheetId']
            break
    
    if not sheet_id:
        print(f"Sheet '{sheet_name}' not found")
        return f"Sheet '{sheet_name}' is already deleted or does not exist"

    request_body = {
        'requests' : [{
            'deleteSheet': {
                'sheetId': sheet_id
            }
        }]
    }
    try:
        response = ctx.deps.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=ctx.deps.spreadsheet_id,
            body=request_body
        ).execute()
        return response
    except (Exception, UnexpectedModelBehavior) as e:
        return f'An error occured {str(e)}'

    except ssl.SSL_ERROR_SSL as e:
        raise ModelRetry(f'An error occured: {str(e)}. Please try again')

@sheets_agent.tool(retries=2)
def list_sheets(ctx: RunContext[SheetsDependencies]) -> List[Dict[str, Any]]:
    try:
        print('Calling list_sheets')
        sheet_metadata = ctx.deps.sheets_service.spreadsheets().get(spreadsheetId=ctx.deps.spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        if not sheets:
            return 'No sheets found'
        sheet_list = [{'id': sheet['properties']['sheetId'], 'name': sheet['properties']['title']} for sheet in sheets]
        return sheet_list
    except ssl.SSL_ERROR_SSL as e:
        raise ModelRetry(f'An error occured: {str(e)}. Please try again')

if __name__ == "__main__":
    SPREADSHEET_ID = '1H81qVQM5qnSLOKiX9cs1BgYL6p4KbRxwwaUZOi-fjB4'

    service = init_google_sheets_client()

    deps = SheetsDependencies(service, SPREADSHEET_ID)

    import sys

    prompt = input('User: ')
    if prompt.lower() == 'exit':
        sys.exit('See you next time')

    response = sheets_agent.run_sync(prompt.strip(), deps=deps)
    print(f'Sheets Agent: {response.output}')

    while True:
        prompt = input('User: ')
        if prompt.lower() == 'exit':
            sys.exit('See you next time') 
        #response = sheets_agetn.run_sync(prompt.strip(), deps=deps, message_history=response.all_messages())
        response = sheets_agent.run_sync(prompt.strip(), deps=deps)
        print(f'Sheets Agent: {response.output.result_details}')