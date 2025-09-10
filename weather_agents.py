from typing import Any 
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext
from load_models import GEMINI_MODEL

class Deps(BaseModel):
    """ Default Dependencies """
    weather_api_key: str | None = Field(title='Weather API key', description='weather api key')
    geo_api_key: str | None = Field(title='Geo API key', description='geo service api key')

weather_agent = Agent(
    name='Weather Agent',
    model=GEMINI_MODEL,
    system_prompt=(
        'Be concise reply one sentence'
        'Use the `get_lat_lang` tool to get the latitude and longitude of the locations, '
        'then use the `get_weather` tool to get the weather.'
    ),
    deps_type=Deps,
    #result_type=<response object>,
)


@weather_agent.tool
def get_lat_lang(ctx: RunContext[Deps], location_description:str
) -> dict[str,float]:
    """Get the latitude and longitude of the location. 
    Args:
        ctx: The context.
        location_description: A description of a location.
    """

    params = {
        'q': location_description,
        'api_key': ctx.deps.geo_api_key,
    }

    print('params passed by the agent:', params)

    #Simulate an api call to get the latitude and longitude
    if 'London' in location_description:
        return {'lat': 10.795323, 'lng': -55.393958}
    elif 'San Francisco' in location_description:
        return {'lat': 37.7749, 'lng': -122.4194}
    else:
        raise ModelRetry('Could not find the location')

@weather_agent.tool
def get_weather(ctx: RunContext[Deps], lat: float, lng:float) -> dict[str, Any]:
    """
    Get the weather at a location.

    Args:
        ctx: The context
        lat: The latitude of the location
        lng: The longitude of the location
    """
    if lat == 0 and lng == 0:
        raise ModelRetry('Could not find the location')

    params = {
        'lat': lat,
        'lng': lng,
        'api_key': ctx.deps.weather_api_key,
    }
    print(f"lat: {lat}, and lng: {lng}")
    #Simulate an api cll to get the weather info
    if lat == 10.795323 and lng == -55.393958:
        return {'temp': 70, 'description': 'Snowing'}
    elif lat == 37.7749 and lng == -122.4194:
        return {'temp': 100, 'description': 'Windy'}


if __name__ == "__main__":
    deps = Deps(weather_api_key='<weather_api_key>', geo_api_key='<geo_api_key>')

    result = weather_agent.run_sync(
        'What is the weather like in London and in San Francisco, CA?',
        deps=deps
    )

    print('------')
    print('Result:')
    print(result)
